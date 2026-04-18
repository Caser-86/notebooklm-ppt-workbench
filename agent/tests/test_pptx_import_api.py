import json
from pathlib import Path

from fastapi.testclient import TestClient
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from sqlmodel import Session, select

import app.db as db_module
from app.main import app
from app.models import Job
from app.services.artifacts import ARTIFACTS_ROOT
from app.worker import run_job_handler


PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def run_job(job_id: int) -> dict:
    with Session(db_module.engine) as session:
        job = session.exec(select(Job).where(Job.id == job_id)).first()
        assert job is not None
        run_job_handler(session, job)
        session.refresh(job)
        return {"status": job.status, "result_json": json.loads(job.result_json or "{}")}


def test_upload_pptx_creates_import_record(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "PPTX Import", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("demo.pptx", ["Editable rebuild"])

    with pptx_path.open("rb") as handle:
        response = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("demo.pptx", handle, PPTX_MIME)},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["job_id"] > 0

    job_result = run_job(body["job_id"])
    assert job_result["status"] == "succeeded"
    assert job_result["result_json"]["import_id"] > 0


def test_imported_pptx_can_be_rebuilt_into_artifacts(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Import Flow", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("flow.pptx", ["Editable rebuild"])

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("flow.pptx", handle, PPTX_MIME)},
        ).json()

    import_job_result = run_job(imported["job_id"])
    import_id = import_job_result["result_json"]["import_id"]

    response = client.post(f"/imports/{import_id}/rebuild")

    assert response.status_code == 202
    rebuild_job_result = run_job(response.json()["job_id"])
    assert rebuild_job_result["status"] == "succeeded"
    assert {artifact["id"] for artifact in rebuild_job_result["result_json"]["artifacts"]} == {"display-clone", "editable-rebuild"}


def test_imported_multi_slide_pptx_preserves_slide_count_in_rebuild(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Import Flow", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("multi-slide.pptx", ["Editable rebuild", "NotebookLM export"])

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("multi-slide.pptx", handle, PPTX_MIME)},
        ).json()

    import_job_result = run_job(imported["job_id"])
    rebuild = client.post(f"/imports/{import_job_result['result_json']['import_id']}/rebuild")

    assert rebuild.status_code == 202
    run_job(rebuild.json()["job_id"])

    display_path = ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "display-clone.pptx"
    editable_path = ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "editable-rebuild.pptx"

    assert len(Presentation(display_path).slides) == 2
    assert len(Presentation(editable_path).slides) == 2


def test_imported_table_rebuild_stays_editable_table(build_fixture_pptx_with_table):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Table Import", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_table("table-import.pptx")

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("table-import.pptx", handle, PPTX_MIME)},
        ).json()

    import_job_result = run_job(imported["job_id"])
    rebuild = client.post(f"/imports/{import_job_result['result_json']['import_id']}/rebuild")

    assert rebuild.status_code == 202
    run_job(rebuild.json()["job_id"])
    editable_path = ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "editable-rebuild.pptx"
    presentation = Presentation(editable_path)

    assert any(shape.has_table for shape in presentation.slides[0].shapes if shape.shape_type == MSO_SHAPE_TYPE.TABLE)


def test_imported_chart_counts_appear_in_import_summary(build_fixture_pptx_with_chart):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Chart Import", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_chart("chart-summary.pptx")

    with pptx_path.open("rb") as handle:
        queued = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("chart-summary.pptx", handle, PPTX_MIME)},
        ).json()

    run_job(queued["job_id"])

    imports = client.get(f"/projects/{project['id']}/imports").json()

    assert imports[0]["object_summary"]["imported_chart"] == 1
    assert imports[0]["slide_assets"][0]["object_summary"]["imported_chart"] == 1


def test_imported_chart_rebuild_preserves_chart_presence(build_fixture_pptx_with_chart):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Chart Rebuild", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_chart("chart-rebuild.pptx")

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("chart-rebuild.pptx", handle, PPTX_MIME)},
        ).json()

    import_job_result = run_job(imported["job_id"])
    response = client.post(f"/imports/{import_job_result['result_json']['import_id']}/rebuild")

    assert response.status_code == 202
    run_job(response.json()["job_id"])
    editable = Presentation(ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "editable-rebuild.pptx")
    assert any(shape.has_table for shape in editable.slides[0].shapes if shape.shape_type == MSO_SHAPE_TYPE.TABLE)


def test_imported_group_counts_appear_in_import_summary(build_fixture_pptx_with_group_shape):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Group Import", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_group_shape("group-summary.pptx")

    with pptx_path.open("rb") as handle:
        queued = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("group-summary.pptx", handle, PPTX_MIME)},
        ).json()

    run_job(queued["job_id"])

    imports = client.get(f"/projects/{project['id']}/imports").json()

    assert imports[0]["object_summary"]["unsupported_group"] >= 1
    assert imports[0]["slide_assets"][0]["object_summary"]["unsupported_group"] >= 1


def test_unsupported_group_rebuild_preserves_group_presence(build_fixture_pptx_with_group_shape):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Group Rebuild", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx_with_group_shape("group-rebuild.pptx")

    with pptx_path.open("rb") as handle:
        imported = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("group-rebuild.pptx", handle, PPTX_MIME)},
        ).json()

    import_job_result = run_job(imported["job_id"])
    response = client.post(f"/imports/{import_job_result['result_json']['import_id']}/rebuild")

    assert response.status_code == 202
    run_job(response.json()["job_id"])
    editable = Presentation(ARTIFACTS_ROOT / str(project["id"]) / "rebuild-001" / "editable-rebuild.pptx")
    slide_texts = [shape.text for shape in editable.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]

    assert any("Unsupported grouped content" in text for text in slide_texts)
