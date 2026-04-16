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
