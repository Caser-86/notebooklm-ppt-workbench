from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.jobs import router as jobs_router
from app.api.projects import router as projects_router
from app.db import init_db
from app.services.artifacts import ARTIFACTS_ROOT

app = FastAPI(
    title="NotebookLM PPT 代理",
    description="用于 NotebookLM 半自动工作流与 PPT 重建的本地代理服务。",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()
app.include_router(projects_router)
app.include_router(jobs_router)
ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/artifacts", StaticFiles(directory=ARTIFACTS_ROOT), name="artifacts")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
