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
