from pathlib import Path

ARTIFACTS_ROOT = Path(__file__).resolve().parents[2] / "data" / "artifacts"


def ensure_project_artifact_dir(project_id: int) -> Path:
    path = ARTIFACTS_ROOT / str(project_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_href(project_id: int, filename: str) -> str:
    return f"/artifacts/{project_id}/{filename}"


def ensure_rebuild_version_dir(project_id: int, version_number: int) -> Path:
    path = ensure_project_artifact_dir(project_id) / f"rebuild-{version_number:03d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_version_href(project_id: int, version_number: int, filename: str) -> str:
    return f"/artifacts/{project_id}/rebuild-{version_number:03d}/{filename}"
