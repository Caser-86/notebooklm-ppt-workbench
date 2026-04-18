import json
from pathlib import Path

from sqlmodel import Session, select

from app.models import ImportedPresentation, ImportedSlideAsset, Project, RebuildVersion, SourceRevision
from app.services.artifacts import (
    artifact_version_href,
    ensure_import_dir,
    ensure_rebuild_version_dir,
)
from app.services.source_ingest import build_source_bundle, summarize_source_bundle
from app.services.pptx_import import extract_pptx_assets
from app.services.reconstruct.display_clone import build_display_clone
from app.services.reconstruct.editable_rebuild import build_editable_rebuild


def handle_import_pptx(session: Session, project_id: int, file_path: str, filename: str) -> dict:
    record = ImportedPresentation(
        project_id=project_id,
        filename=filename,
        original_file_path=file_path,
        status="uploaded",
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    import_id = record.id or 0
    import_dir = ensure_import_dir(project_id, import_id)
    pptx_path = Path(file_path)
    bundle = extract_pptx_assets(project_id, pptx_path, import_dir)
    record.source_type = bundle.source_type
    record.page_count = bundle.page_count
    record.status = "ready"
    session.add(record)

    for slide in bundle.slides:
        structure_json_path = ""
        if slide.blocks:
            structure_path = import_dir / f"slide-{slide.slide_index}-structure.json"
            structure_path.write_text(json.dumps(slide.blocks, ensure_ascii=False), encoding="utf-8")
            structure_json_path = str(structure_path)
        session.add(
            ImportedSlideAsset(
                import_id=import_id,
                slide_index=slide.slide_index,
                preview_image_path=slide.preview_image_path,
                text_dump=slide.text_dump,
                structure_json_path=structure_json_path,
            )
        )
    session.commit()
    return {"import_id": import_id}


def handle_rebuild_import(session: Session, import_id: int) -> dict:
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

    normalized_blocks = []
    for asset in slide_assets:
        if asset.structure_json_path:
            structure_path = Path(asset.structure_json_path)
            if structure_path.exists():
                normalized_blocks.extend(json.loads(structure_path.read_text(encoding="utf-8")))
                continue

        cursor_y = 1.0
        for line in [line for line in asset.text_dump.splitlines() if line.strip()]:
            normalized_blocks.append(
                {
                    "text": line,
                    "content_type": "text",
                    "slide_index": asset.slide_index,
                    "x": 1,
                    "y": cursor_y,
                    "width": 8,
                    "height": 0.6,
                    "font_size": 24 if cursor_y == 1.0 else 16,
                }
            )
            cursor_y += 0.8
    if not normalized_blocks:
        normalized_blocks = [
            {
                "text": imported.filename,
                "content_type": "text",
                "slide_index": 1,
                "x": 1,
                "y": 1,
                "width": 8,
                "height": 0.8,
                "font_size": 24,
            }
        ]

    build_display_clone(slide_paths, display_path)
    build_editable_rebuild(normalized_blocks, editable_path)

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


def handle_analyze_sources(
    session: Session,
    project_id: int,
    prompt: str,
    urls: list[str],
    file_paths: list[str],
    image_paths: list[str],
    audio_paths: list[str],
    video_paths: list[str],
) -> dict:
    bundle = build_source_bundle(
        prompt=prompt,
        urls=urls,
        file_paths=[Path(path) for path in file_paths],
        image_paths=[Path(path) for path in image_paths],
        audio_paths=[Path(path) for path in audio_paths],
        video_paths=[Path(path) for path in video_paths],
    )
    source_manifest = {
        "prompt": bundle.prompt,
        "urls": bundle.urls,
        "file_paths": bundle.file_paths,
        "image_paths": bundle.image_paths,
        "audio_paths": bundle.audio_paths,
        "video_paths": bundle.video_paths,
    }
    insight_summary = summarize_source_bundle(bundle)

    project = session.get(Project, project_id)
    assert project is not None
    current_max = session.exec(
        select(SourceRevision.revision_number)
        .where(SourceRevision.project_id == project_id)
        .order_by(SourceRevision.revision_number.desc())
    ).first()
    revision_number = (current_max or 0) + 1

    project.source_manifest_json = json.dumps(source_manifest)
    project.insight_summary = insight_summary
    session.add(project)
    session.add(
        SourceRevision(
            project_id=project_id,
            revision_number=revision_number,
            source_manifest_json=json.dumps(source_manifest),
            insight_summary=insight_summary,
        )
    )
    session.commit()

    return {
        "revision_number": revision_number,
        "source_manifest": source_manifest,
        "insight_summary": insight_summary,
    }
