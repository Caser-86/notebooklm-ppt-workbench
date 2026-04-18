from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.jobs import router as jobs_router
from app.api.projects import router as projects_router
from app.db import init_db
from app.services.artifacts import ARTIFACTS_ROOT

app = FastAPI(
    title="NotebookLM PPT 代理",
    description="用于 NotebookLM 半自动工作流与 PPT 重建的本地代理服务。",
)
init_db()
app.include_router(projects_router)
app.include_router(jobs_router)
ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_ROOT), name="artifacts")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
