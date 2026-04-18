import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import ImportedPresentation, ImportedSlideAsset, Job, RebuildVersion
from app.api.projects import serialize_import_record
from app.services.artifacts import (
    artifact_href,
    artifact_version_href,
    ensure_project_artifact_dir,
    ensure_import_dir,
    ensure_rebuild_version_dir,
)
from app.services.reconstruct.editable_rebuild import build_editable_rebuild
from app.services.reconstruct.display_clone import build_display_clone
from app.schemas import ImportedPresentationRead, JobCreate
from app.services.notebooklm import run_generation
from app.services.pptx_import import extract_pptx_assets
from app.services.prompts import build_generation_prompt, get_prompt_presets

router = APIRouter(tags=["jobs"])


class LaunchGenerateJob(BaseModel):
    preset_id: str
    user_prompt: str
    source_summary: str


@router.post("/projects/{project_id}/jobs", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(project_id: int, payload: JobCreate, session: Session = Depends(get_session)) -> Job:
    job = Job(project_id=project_id, **payload.model_dump())
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.get("/prompt-presets")
def list_prompt_presets():
    return get_prompt_presets()


@router.post("/projects/{project_id}/jobs/generate")
def launch_generate_job(project_id: int, payload: LaunchGenerateJob):
    prompt = build_generation_prompt(payload.preset_id, payload.user_prompt, payload.source_summary)
    return {"project_id": project_id, "status": "ready_to_generate", "prompt": prompt}


@router.post("/jobs/{job_id}/run")
def run_job(job_id: int, browser_ready: bool = True):
    result = run_generation({"mode": "auto", "browser_ready": browser_ready, "prompt": ""})
    return {"job_id": job_id, **result}


@router.post("/projects/{project_id}/rebuild/display-clone")
def rebuild_display_clone(project_id: int, slide_paths: list[str]):
    output_path = ensure_project_artifact_dir(project_id) / "display-clone.pptx"
    build_display_clone([Path(path) for path in slide_paths], output_path)
    return {"project_id": project_id, "artifact": str(output_path)}


@router.post("/projects/{project_id}/imports/pptx", response_model=ImportedPresentationRead, status_code=status.HTTP_201_CREATED)
async def upload_pptx_import(
    project_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    record = ImportedPresentation(
        project_id=project_id,
        filename=file.filename or "upload.pptx",
        original_file_path="",
        status="uploaded",
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    import_id = record.id or 0
    import_dir = ensure_import_dir(project_id, import_id)
    pptx_path = import_dir / record.filename
    pptx_path.write_bytes(await file.read())

    bundle = extract_pptx_assets(project_id, pptx_path, import_dir)
    record.original_file_path = str(pptx_path)
    record.source_type = bundle.source_type
    record.page_count = bundle.page_count
    record.status = "ready"
    session.add(record)

    for slide in bundle.slides:
        session.add(
            ImportedSlideAsset(
                import_id=import_id,
                slide_index=slide.slide_index,
                preview_image_path=slide.preview_image_path,
                text_dump=slide.text_dump,
                structure_json_path=slide.structure_json_path,
            )
        )
    session.commit()
    session.refresh(record)

    return serialize_import_record(record, session)


@router.post("/imports/{import_id}/rebuild")
def rebuild_from_import(import_id: int, session: Session = Depends(get_session)):
    imported = session.get(ImportedPresentation, import_id)
    assert imported is not None
    slide_assets = list(
        session.exec(
            select(ImportedSlideAsset)
            .where(ImportedSlideAsset.import_id == import_id)
            .order_by(ImportedSlideAsset.slide_index.asc())
        )
    )
    current_max = session.exec(
        select(RebuildVersion.version_number)
        .where(RebuildVersion.project_id == imported.project_id)
        .order_by(RebuildVersion.version_number.desc())
    ).first()
    version_number = (current_max or 0) + 1
    artifact_dir = ensure_rebuild_version_dir(imported.project_id, version_number)

    slide_paths = [Path(asset.preview_image_path) for asset in slide_assets]
    display_path = artifact_dir / "display-clone.pptx"
    editable_path = artifact_dir / "editable-rebuild.pptx"

    ocr_blocks = []
    for asset in slide_assets:
        cursor_y = 1.0
        for line in [line for line in asset.text_dump.splitlines() if line.strip()]:
            ocr_blocks.append(
                {
                    "text": line,
                    "slide_index": asset.slide_index,
                    "x": 1,
                    "y": cursor_y,
                    "width": 8,
                    "height": 0.6,
                    "font_size": 24 if cursor_y == 1.0 else 16,
                }
            )
            cursor_y += 0.8
    if not ocr_blocks:
        ocr_blocks = [
            {
                "text": imported.filename,
                "slide_index": 1,
                "x": 1,
                "y": 1,
                "width": 8,
                "height": 0.8,
                "font_size": 24,
            }
        ]

    build_display_clone(slide_paths, display_path)
    build_editable_rebuild(ocr_blocks, editable_path)

    rebuild = RebuildVersion(
        project_id=imported.project_id,
        version_number=version_number,
        slide_count=len(slide_paths),
        display_clone_path=str(display_path),
        editable_rebuild_path=str(editable_path),
    )
    session.add(rebuild)
    imported.status = "completed"
    session.add(imported)
    session.commit()

    return {
        "project_id": imported.project_id,
        "version_number": version_number,
        "artifacts": [
            {
                "id": "display-clone",
                "label": "Display clone",
                "href": artifact_version_href(imported.project_id, version_number, display_path.name),
            },
            {
                "id": "editable-rebuild",
                "label": "Editable rebuild",
                "href": artifact_version_href(imported.project_id, version_number, editable_path.name),
            },
        ],
    }


@router.post("/projects/{project_id}/rebuild/manual-export")
async def rebuild_manual_export(
    project_id: int,
    slide_images: list[UploadFile] = File(...),
    ocr_json: UploadFile | None = File(default=None),
    session: Session = Depends(get_session),
):
    current_max = session.exec(
        select(RebuildVersion.version_number)
        .where(RebuildVersion.project_id == project_id)
        .order_by(RebuildVersion.version_number.desc())
    ).first()
    version_number = (current_max or 0) + 1
    artifact_dir = ensure_rebuild_version_dir(project_id, version_number)
    saved_slide_paths: list[Path] = []

    for image in slide_images:
        destination = artifact_dir / image.filename
        destination.write_bytes(await image.read())
        saved_slide_paths.append(destination)

    if ocr_json is not None:
        ocr_blocks = json.loads((await ocr_json.read()).decode("utf-8"))
    else:
        ocr_blocks = [{"text": "Editable rebuild", "x": 1, "y": 1, "width": 4, "height": 1, "font_size": 24}]

    display_path = artifact_dir / "display-clone.pptx"
    editable_path = artifact_dir / "editable-rebuild.pptx"

    build_display_clone(saved_slide_paths, display_path)
    build_editable_rebuild(ocr_blocks, editable_path)

    rebuild = RebuildVersion(
        project_id=project_id,
        version_number=version_number,
        slide_count=len(saved_slide_paths),
        display_clone_path=str(display_path),
        editable_rebuild_path=str(editable_path),
    )
    session.add(rebuild)
    session.commit()

    return {
        "project_id": project_id,
        "version_number": version_number,
        "artifacts": [
            {
                "id": "display-clone",
                "label": "Display clone",
                "href": artifact_version_href(project_id, version_number, display_path.name),
            },
            {
                "id": "editable-rebuild",
                "label": "Editable rebuild",
                "href": artifact_version_href(project_id, version_number, editable_path.name),
            },
        ],
    }
