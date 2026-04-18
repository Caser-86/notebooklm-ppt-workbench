import json

from sqlmodel import Session, SQLModel, create_engine, select

import app.db as db_module
from app.models import Job
from app.models import ImportedPresentation
from app.services.job_queue import claim_next_job, enqueue_job
from app.worker import run_job_handler


def test_claim_next_job_marks_job_running(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'worker.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(Job(project_id=1, job_type="import_pptx", status="queued"))
        session.commit()

        claimed = claim_next_job(session, worker_id="worker-1")

        assert claimed is not None
        assert claimed.status == "running"
        assert claimed.locked_by == "worker-1"
        assert claimed.started_at is not None


def test_run_job_handler_executes_import_pptx_job(tmp_path, build_fixture_pptx):
    pptx_path = build_fixture_pptx("worker-import.pptx", ["Editable rebuild"])

    with Session(db_module.engine) as session:
        job = enqueue_job(
            session,
            project_id=1,
            job_type="import_pptx",
            payload={"file_path": str(pptx_path), "filename": "worker-import.pptx"},
        )

    with Session(db_module.engine) as session:
        stored_job = session.exec(select(Job).where(Job.id == job.id)).first()
        assert stored_job is not None
        run_job_handler(session, stored_job)
        session.refresh(stored_job)

        assert stored_job.status == "succeeded"
        result = json.loads(stored_job.result_json)
        assert result["import_id"] > 0
        imported = session.get(ImportedPresentation, result["import_id"])
        assert imported is not None
        assert imported.filename == "worker-import.pptx"
