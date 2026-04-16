from pathlib import Path

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import Project, RebuildVersion
from app.schemas import ArtifactLink, ProjectCreate, RebuildVersionRead
from app.services.artifacts import artifact_version_href
from app.services.source_ingest import build_source_bundle

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


@router.post("/projects/{project_id}/sources")
def submit_sources(project_id: int, payload: SourceSubmit):
    bundle = build_source_bundle(
        prompt=payload.prompt,
        urls=payload.urls,
        file_paths=[Path(path) for path in payload.file_paths],
        image_paths=[Path(path) for path in payload.image_paths],
        audio_paths=[Path(path) for path in payload.audio_paths],
        video_paths=[Path(path) for path in payload.video_paths],
    )
    return {"project_id": project_id, "source_manifest": bundle.__dict__}
