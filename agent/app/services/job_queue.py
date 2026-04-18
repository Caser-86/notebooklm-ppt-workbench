import json
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Job


def enqueue_job(session: Session, project_id: int, job_type: str, payload: dict) -> Job:
    job = Job(
        project_id=project_id,
        job_type=job_type,
        status="queued",
        payload_json=json.dumps(payload),
        result_json="{}",
        error_message="",
        attempt_count=0,
        max_attempts=3,
        available_at=datetime.now(UTC),
        locked_by="",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def claim_next_job(session: Session, worker_id: str) -> Job | None:
    now = datetime.now(UTC)
    statement = (
        select(Job)
        .where(Job.status == "queued")
        .where(Job.available_at <= now)
        .order_by(Job.created_at.asc())
    )
    job = session.exec(statement).first()
    if job is None:
        return None

    job.status = "running"
    job.locked_by = worker_id
    job.locked_at = now
    job.started_at = now
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
