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
from app.schemas import ImportedPresentationRead, JobCreate, JobEnqueueResponse, JobRead
from app.services.job_queue import enqueue_job
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


@router.get("/jobs/{job_id}", response_model=JobRead)
def get_job(job_id: int, session: Session = Depends(get_session)) -> JobRead:
    job = session.get(Job, job_id)
    assert job is not None
    return JobRead(
        id=job.id or 0,
        project_id=job.project_id,
        job_type=job.job_type,
        status=job.status,
        result_json=json.loads(job.result_json or "{}"),
        error_message=job.error_message,
    )


@router.get("/projects/{project_id}/jobs", response_model=list[JobRead])
def list_project_jobs(project_id: int, session: Session = Depends(get_session)) -> list[JobRead]:
    jobs = list(
        session.exec(select(Job).where(Job.project_id == project_id).order_by(Job.created_at.desc()))
    )
    return [
        JobRead(
            id=job.id or 0,
            project_id=job.project_id,
            job_type=job.job_type,
            status=job.status,
            result_json=json.loads(job.result_json or "{}"),
            error_message=job.error_message,
        )
        for job in jobs
    ]


@router.post("/projects/{project_id}/imports/pptx", response_model=JobEnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_pptx_import(
    project_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    artifact_dir = ensure_project_artifact_dir(project_id) / "queued"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or "upload.pptx"
    pptx_path = artifact_dir / filename
    pptx_path.write_bytes(await file.read())
    job = enqueue_job(
        session,
        project_id=project_id,
        job_type="import_pptx",
        payload={"file_path": str(pptx_path), "filename": filename},
    )
    return JobEnqueueResponse(job_id=job.id or 0, status=job.status)


@router.post("/imports/{import_id}/rebuild", response_model=JobEnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
def rebuild_from_import(import_id: int, session: Session = Depends(get_session)):
    imported = session.get(ImportedPresentation, import_id)
    assert imported is not None
    job = enqueue_job(
        session,
        project_id=imported.project_id,
        job_type="rebuild_import",
        payload={"import_id": import_id},
    )
    return JobEnqueueResponse(job_id=job.id or 0, status=job.status)


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
