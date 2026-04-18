from fastapi.testclient import TestClient

from app.main import app


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

    assert submit_response.status_code == 200
    submit_body = submit_response.json()
    assert submit_body["source_manifest"]["urls"] == ["https://example.com/launch"]
    normalized_file_path = source_file.as_posix()
    assert submit_body["source_manifest"]["file_paths"] == [normalized_file_path]
    assert submit_body["source_manifest"]["image_paths"] == ["D:/media/launch-cover.png"]
    assert submit_body["source_manifest"]["audio_paths"] == ["D:/media/launch-voice.mp3"]
    assert submit_body["source_manifest"]["video_paths"] == ["D:/media/launch-demo.mp4"]
    assert "1 url" in submit_body["insight_summary"].lower()
    assert "1 image" in submit_body["insight_summary"].lower()
    assert "1 audio" in submit_body["insight_summary"].lower()
    assert "1 video" in submit_body["insight_summary"].lower()

    detail_response = client.get(f"/projects/{project['id']}")
    detail = detail_response.json()
    assert detail["source_manifest"]["file_paths"] == [normalized_file_path]
    assert detail["source_manifest"]["image_paths"] == ["D:/media/launch-cover.png"]
    assert detail["source_manifest"]["audio_paths"] == ["D:/media/launch-voice.mp3"]
    assert detail["source_manifest"]["video_paths"] == ["D:/media/launch-demo.mp4"]
    assert detail["insight_summary"] == submit_body["insight_summary"]

    history_response = client.get(f"/projects/{project['id']}/sources/history")
    history = history_response.json()
    assert history[0]["revision_number"] == 1
    assert history[0]["source_manifest"]["urls"] == ["https://example.com/launch"]
    assert history[0]["insight_summary"] == submit_body["insight_summary"]


def test_project_import_history_returns_import_records():
    client = TestClient(app)
    project = client.post("/projects", json={"title": "Import Demo", "preferred_language": "zh-CN"}).json()

    response = client.get(f"/projects/{project['id']}/imports")

    assert response.status_code == 200
    assert response.json() == []
