import socket
import time

from sqlmodel import Session

from app.db import engine
from app.services.job_queue import claim_next_job


def run_job_handler(session: Session, job) -> None:
    job.status = "succeeded"
    session.add(job)
    session.commit()


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
