import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Project, RebuildVersion, SourceRevision
from app.schemas import ArtifactLink, ProjectCreate, ProjectDetailRead, ProjectUpdate, RebuildVersionRead, SourceRevisionRead
from app.services.artifacts import artifact_version_href
from app.services.source_ingest import build_source_bundle, summarize_source_bundle

router = APIRouter(tags=["projects"])


class SourceSubmit(BaseModel):
    prompt: str
    urls: list[str] = []
    file_paths: list[str] = []
    image_paths: list[str] = []
    audio_paths: list[str] = []
    video_paths: list[str] = []


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)) -> Project:
    project = Project(**payload.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/projects", response_model=list[Project])
def list_projects(session: Session = Depends(get_session)) -> list[Project]:
    statement = select(Project).order_by(Project.created_at.desc())
    return list(session.exec(statement))


@router.get("/projects/{project_id}", response_model=ProjectDetailRead)
def get_project(project_id: int, session: Session = Depends(get_session)) -> ProjectDetailRead:
    project = session.get(Project, project_id)
    assert project is not None
    return ProjectDetailRead(
        id=project.id or 0,
        title=project.title,
        preferred_language=project.preferred_language,
        preferred_style=project.preferred_style,
        brief=project.brief,
        prompt_draft=project.prompt_draft,
        source_manifest=json.loads(project.source_manifest_json or "{}"),
        insight_summary=project.insight_summary,
    )


@router.put("/projects/{project_id}", response_model=ProjectDetailRead)
def update_project(project_id: int, payload: ProjectUpdate, session: Session = Depends(get_session)) -> ProjectDetailRead:
    project = session.get(Project, project_id)
    assert project is not None
    project.brief = payload.brief
    project.prompt_draft = payload.prompt_draft
    project.source_manifest_json = json.dumps(payload.source_manifest)
    project.updated_at = datetime.now(UTC)
    session.add(project)
    session.commit()
    session.refresh(project)
    return ProjectDetailRead(
        id=project.id or 0,
        title=project.title,
        preferred_language=project.preferred_language,
        preferred_style=project.preferred_style,
        brief=project.brief,
        prompt_draft=project.prompt_draft,
        source_manifest=json.loads(project.source_manifest_json or "{}"),
        insight_summary=project.insight_summary,
    )


@router.get("/projects/{project_id}/rebuilds", response_model=list[RebuildVersionRead])
def list_project_rebuilds(project_id: int, session: Session = Depends(get_session)) -> list[RebuildVersionRead]:
    statement = select(RebuildVersion).where(RebuildVersion.project_id == project_id).order_by(RebuildVersion.version_number.desc())
    rebuilds = list(session.exec(statement))
    return [
        RebuildVersionRead(
            id=rebuild.id or 0,
            version_number=rebuild.version_number,
            slide_count=rebuild.slide_count,
            artifacts=[
                ArtifactLink(
                    id="display-clone",
                    label="Display clone",
                    href=artifact_version_href(project_id, rebuild.version_number, Path(rebuild.display_clone_path).name),
                ),
                ArtifactLink(
                    id="editable-rebuild",
                    label="Editable rebuild",
                    href=artifact_version_href(project_id, rebuild.version_number, Path(rebuild.editable_rebuild_path).name),
                ),
            ],
        )
        for rebuild in rebuilds
    ]


@router.get("/projects/{project_id}/sources/history", response_model=list[SourceRevisionRead])
def list_project_source_history(project_id: int, session: Session = Depends(get_session)) -> list[SourceRevisionRead]:
    statement = select(SourceRevision).where(SourceRevision.project_id == project_id).order_by(SourceRevision.revision_number.desc())
    revisions = list(session.exec(statement))
    return [
        SourceRevisionRead(
            id=revision.id or 0,
            revision_number=revision.revision_number,
            source_manifest=json.loads(revision.source_manifest_json or "{}"),
            insight_summary=revision.insight_summary,
        )
        for revision in revisions
    ]


@router.post("/projects/{project_id}/sources")
def submit_sources(project_id: int, payload: SourceSubmit, session: Session = Depends(get_session)):
    bundle = build_source_bundle(
        prompt=payload.prompt,
        urls=payload.urls,
        file_paths=[Path(path) for path in payload.file_paths],
        image_paths=[Path(path) for path in payload.image_paths],
        audio_paths=[Path(path) for path in payload.audio_paths],
        video_paths=[Path(path) for path in payload.video_paths],
    )
    project = session.get(Project, project_id)
    assert project is not None

    source_manifest = {
        "prompt": bundle.prompt,
        "urls": bundle.urls,
        "file_paths": bundle.file_paths,
        "image_paths": bundle.image_paths,
        "audio_paths": bundle.audio_paths,
        "video_paths": bundle.video_paths,
    }
    insight_summary = summarize_source_bundle(bundle)

    current_max = session.exec(
        select(SourceRevision.revision_number)
        .where(SourceRevision.project_id == project_id)
        .order_by(SourceRevision.revision_number.desc())
    ).first()
    revision_number = (current_max or 0) + 1

    project.source_manifest_json = json.dumps(source_manifest)
    project.insight_summary = insight_summary
    project.updated_at = datetime.now(UTC)
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
        "project_id": project_id,
        "revision_number": revision_number,
        "source_manifest": source_manifest,
        "insight_summary": insight_summary,
    }
