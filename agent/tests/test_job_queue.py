from datetime import UTC, datetime

from sqlmodel import SQLModel, Session, create_engine

from app.models import Job


def test_job_queue_fields_persist(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'jobs.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        job = Job(
            project_id=1,
            job_type="import_pptx",
            status="queued",
            payload_json="{}",
            result_json="{}",
            error_message="",
            attempt_count=0,
            max_attempts=3,
            available_at=datetime.now(UTC),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        assert job.id is not None
        assert job.status == "queued"
        assert job.payload_json == "{}"
        assert job.result_json == "{}"
        assert job.max_attempts == 3
        assert job.available_at is not None
