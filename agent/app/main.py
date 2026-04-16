from fastapi import FastAPI

from app.api.jobs import router as jobs_router
from app.api.projects import router as projects_router
from app.db import init_db

app = FastAPI(title="NotebookLM PPT Agent")
init_db()
app.include_router(projects_router)
app.include_router(jobs_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
