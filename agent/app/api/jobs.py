from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.models import Job
from app.services.reconstruct.display_clone import build_display_clone
from app.schemas import JobCreate
from app.services.notebooklm import run_generation
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
    from pathlib import Path

    output_path = Path(f"agent/data/artifacts/{project_id}/display-clone.pptx")
    build_display_clone([Path(path) for path in slide_paths], output_path)
    return {"project_id": project_id, "artifact": str(output_path)}
