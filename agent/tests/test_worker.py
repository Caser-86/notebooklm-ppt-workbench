from sqlmodel import Session, SQLModel, create_engine

from app.models import Job
from app.services.job_queue import claim_next_job


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
