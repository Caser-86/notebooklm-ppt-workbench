from pathlib import Path

from fastapi.testclient import TestClient
from pptx import Presentation

from app.main import app
from app.services.artifacts import ARTIFACTS_ROOT


PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def test_upload_pptx_creates_import_record(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "PPTX Import", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("demo.pptx", ["Editable rebuild"])

    with pptx_path.open("rb") as handle:
        response = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("demo.pptx", handle, PPTX_MIME)},
        )

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["filename"] == "demo.pptx"
    assert body["status"] == "ready"
    assert body["page_count"] == 1


def test_imported_pptx_can_be_rebuilt_into_artifacts(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Import Flow", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("flow.pptx", ["Editable rebuild"])

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("flow.pptx", handle, PPTX_MIME)},
        ).json()

    response = client.post(f"/imports/{imported['id']}/rebuild")

    assert response.status_code == 200
    assert {artifact["id"] for artifact in response.json()["artifacts"]} == {"display-clone", "editable-rebuild"}


def test_imported_multi_slide_pptx_preserves_slide_count_in_rebuild(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Import Flow", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("multi-slide.pptx", ["Editable rebuild", "NotebookLM export"])

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("multi-slide.pptx", handle, PPTX_MIME)},
        ).json()

    rebuild = client.post(f"/imports/{imported['id']}/rebuild")

    assert rebuild.status_code == 200

    display_path = ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "display-clone.pptx"
    editable_path = ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "editable-rebuild.pptx"

    assert len(Presentation(display_path).slides) == 2
    assert len(Presentation(editable_path).slides) == 2
