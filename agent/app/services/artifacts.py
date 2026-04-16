from pathlib import Path


def ensure_project_artifact_dir(project_id: int) -> Path:
    path = Path("agent/data/artifacts") / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path
