from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import Job
from app.schemas import JobCreate
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
