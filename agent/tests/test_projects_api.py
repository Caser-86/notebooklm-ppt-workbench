import json

from fastapi.testclient import TestClient
from sqlmodel import Session, select

import app.db as db_module
from app.main import app
from app.models import Job
from app.worker import run_job_handler

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def test_create_project_returns_project_payload():
    client = TestClient(app)
    response = client.post("/projects", json={"title": "Launch deck", "preferred_language": "zh-CN"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Launch deck"
    assert body["preferred_language"] == "zh-CN"
    assert body["id"] > 0


def test_create_job_returns_draft_status():
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Launch deck", "preferred_language": "zh-CN"}).json()

    response = client.post(f"/projects/{project['id']}/jobs", json={"job_type": "generate", "mode": "auto"})

    assert response.status_code == 201
    assert response.json()["status"] == "draft"


def test_project_job_list_returns_created_jobs():
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Queue deck", "preferred_language": "zh-CN"}).json()
    created = client.post(f"/projects/{project['id']}/jobs", json={"job_type": "generate", "mode": "auto"}).json()

    response = client.get(f"/projects/{project['id']}/jobs")

    assert response.status_code == 200
    assert any(
        job["id"] == created["id"] and job["job_type"] == "generate" and "created_at" in job
        for job in response.json()
    )


def test_retry_failed_job_enqueues_new_job():
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Retry deck", "preferred_language": "zh-CN"}).json()

    with Session(db_module.engine) as session:
        failed_job = Job(
            project_id=project["id"],
            job_type="analyze_sources",
            status="failed",
            payload_json='{"prompt":"retry me","urls":[],"file_paths":[],"image_paths":[],"audio_paths":[],"video_paths":[]}',
            result_json="{}",
            error_message="Original failure",
        )
        session.add(failed_job)
        session.commit()
        session.refresh(failed_job)

    response = client.post(f"/jobs/{failed_job.id}/retry")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["job_id"] != failed_job.id

    with Session(db_module.engine) as session:
        retried_job = session.get(Job, body["job_id"])
        assert retried_job is not None
        assert retried_job.project_id == project["id"]
        assert retried_job.job_type == "analyze_sources"
        assert retried_job.status == "queued"
        assert json.loads(retried_job.payload_json) == json.loads(failed_job.payload_json)


def test_list_projects_returns_created_projects():
    client = TestClient(app)
    created = client.post("/projects", json={"title": "History deck", "preferred_language": "zh-CN"}).json()

    response = client.get("/projects")

    assert response.status_code == 200
    assert any(project["id"] == created["id"] and project["title"] == "History deck" for project in response.json())


def test_project_detail_stores_brief_prompt_and_source_manifest():
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Detail deck", "preferred_language": "zh-CN"}).json()

    update_response = client.put(
        f"/projects/{project['id']}",
        json={
            "brief": "Launch expansion narrative",
            "prompt_draft": "Focus on milestones and risks.",
            "source_manifest": {
                "urls": ["https://example.com"],
                "notes": "Pulled from manual source intake",
            },
        },
    )

    assert update_response.status_code == 200

    detail_response = client.get(f"/projects/{project['id']}")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["brief"] == "Launch expansion narrative"
    assert detail["prompt_draft"] == "Focus on milestones and risks."
    assert detail["source_manifest"]["urls"] == ["https://example.com"]


def test_submit_sources_updates_project_detail_and_source_history(tmp_path):
    client = TestClient(app)
    source_file = tmp_path / "notes.txt"
    source_file.write_text("Key launch milestones and risks.", encoding="utf-8")
    project = client.post("/projects", json={"title": "Source detail deck", "preferred_language": "zh-CN"}).json()

    submit_response = client.post(
        f"/projects/{project['id']}/sources",
        json={
            "prompt": "Launch summary",
            "urls": ["https://example.com/launch"],
            "file_paths": [str(source_file)],
            "image_paths": ["D:/media/launch-cover.png"],
            "audio_paths": ["D:/media/launch-voice.mp3"],
            "video_paths": ["D:/media/launch-demo.mp4"],
        },
    )

    assert submit_response.status_code == 202
    submit_body = submit_response.json()
    assert submit_body["status"] == "queued"

    with Session(db_module.engine) as session:
        job = session.exec(select(Job).where(Job.id == submit_body["job_id"])).first()
        assert job is not None
        run_job_handler(session, job)

    job_result = client.get(f"/jobs/{submit_body['job_id']}").json()["result_json"]
    assert job_result["source_manifest"]["urls"] == ["https://example.com/launch"]
    normalized_file_path = source_file.as_posix()
    assert job_result["source_manifest"]["file_paths"] == [normalized_file_path]
    assert job_result["source_manifest"]["image_paths"] == ["D:/media/launch-cover.png"]
    assert job_result["source_manifest"]["audio_paths"] == ["D:/media/launch-voice.mp3"]
    assert job_result["source_manifest"]["video_paths"] == ["D:/media/launch-demo.mp4"]
    assert "1 url" in job_result["insight_summary"].lower()
    assert "1 image" in job_result["insight_summary"].lower()
    assert "1 audio" in job_result["insight_summary"].lower()
    assert "1 video" in job_result["insight_summary"].lower()

    detail_response = client.get(f"/projects/{project['id']}")
    detail = detail_response.json()
    assert detail["source_manifest"]["file_paths"] == [normalized_file_path]
    assert detail["source_manifest"]["image_paths"] == ["D:/media/launch-cover.png"]
    assert detail["source_manifest"]["audio_paths"] == ["D:/media/launch-voice.mp3"]
    assert detail["source_manifest"]["video_paths"] == ["D:/media/launch-demo.mp4"]
    assert detail["insight_summary"] == job_result["insight_summary"]

    history_response = client.get(f"/projects/{project['id']}/sources/history")
    history = history_response.json()
    assert history[0]["revision_number"] == 1
    assert history[0]["source_manifest"]["urls"] == ["https://example.com/launch"]
    assert history[0]["insight_summary"] == job_result["insight_summary"]


def test_project_import_history_returns_import_records():
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Import Demo", "preferred_language": "zh-CN"}).json()

    response = client.get(f"/projects/{project['id']}/imports")

    assert response.status_code == 200
    assert response.json() == []


def test_project_import_history_returns_slide_object_summary(build_fixture_pptx):
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Preview Demo", "preferred_language": "zh-CN"}).json()
    pptx_path = build_fixture_pptx("preview-demo.pptx", ["Editable rebuild"])

    with pptx_path.open("rb") as handle:
        upload_response = client.post(
            f"/projects/{project['id']}/imports/pptx",
            files={"file": ("preview-demo.pptx", handle, PPTX_MIME)},
        )

    assert upload_response.status_code == 202

    job_id = upload_response.json()["job_id"]
    with Session(db_module.engine) as session:
        job = session.exec(select(Job).where(Job.id == job_id)).first()
        assert job is not None
        run_job_handler(session, job)

    history = client.get(f"/projects/{project['id']}/imports").json()

    assert "object_summary" in history[0]["slide_assets"][0]
