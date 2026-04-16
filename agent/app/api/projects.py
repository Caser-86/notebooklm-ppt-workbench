from pathlib import Path

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import Project
from app.schemas import ProjectCreate
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
