from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.models import Job
from app.schemas import JobCreate

router = APIRouter(tags=["jobs"])


@router.post("/projects/{project_id}/jobs", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(project_id: int, payload: JobCreate, session: Session = Depends(get_session)) -> Job:
    job = Job(project_id=project_id, **payload.model_dump())
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
