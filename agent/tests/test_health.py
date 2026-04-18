from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck_returns_ok():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_preflight_allows_local_web_origin():
    client = TestClient(app)

    response = client.options(
        "/projects",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"
