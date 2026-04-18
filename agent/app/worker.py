import json
import socket
import time

from sqlmodel import Session

from app.db import engine
from app.models import Job
from app.services.job_handlers import handle_analyze_sources, handle_import_pptx, handle_rebuild_import
from app.services.job_queue import claim_next_job, mark_job_failed, mark_job_succeeded


def run_job_handler(session: Session, job: Job) -> None:
    payload = json.loads(job.payload_json or "{}")
    try:
        if job.job_type == "import_pptx":
            result = handle_import_pptx(
                session,
                project_id=job.project_id,
                file_path=payload["file_path"],
                filename=payload["filename"],
            )
        elif job.job_type == "analyze_sources":
            result = handle_analyze_sources(
                session,
                project_id=job.project_id,
                prompt=payload["prompt"],
                urls=payload["urls"],
                file_paths=payload["file_paths"],
                image_paths=payload["image_paths"],
                audio_paths=payload["audio_paths"],
                video_paths=payload["video_paths"],
            )
        elif job.job_type == "rebuild_import":
            result = handle_rebuild_import(session, payload["import_id"])
        else:
            result = {}
        mark_job_succeeded(session, job, result)
    except Exception as exc:  # pragma: no cover - defensive worker boundary
        mark_job_failed(session, job, str(exc), retryable=False)


def main() -> None:
    worker_id = socket.gethostname()
    while True:
        with Session(engine) as session:
            job = claim_next_job(session, worker_id)
            if job is None:
                time.sleep(2)
                continue
            run_job_handler(session, job)


if __name__ == "__main__":
    main()
