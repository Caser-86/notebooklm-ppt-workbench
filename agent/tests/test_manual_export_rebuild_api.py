import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_manual_export_rebuild_returns_download_artifacts():
    client = TestClient(app)
    slide_1 = Path("tests/fixtures/slides/slide-1.png")
    slide_2 = Path("tests/fixtures/slides/slide-2.png")
    ocr = Path("tests/fixtures/ocr_blocks.json")

    with (
        slide_1.open("rb") as slide_1_file,
        slide_2.open("rb") as slide_2_file,
        ocr.open("rb") as ocr_file,
    ):
        response = client.post(
            "/projects/1/rebuild/manual-export",
            files=[
                ("slide_images", ("slide-1.png", slide_1_file, "image/png")),
                ("slide_images", ("slide-2.png", slide_2_file, "image/png")),
                ("ocr_json", ("ocr_blocks.json", ocr_file, "application/json")),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == 1
    assert [artifact["label"] for artifact in body["artifacts"]] == ["Display clone", "Editable rebuild"]
    assert body["artifacts"][0]["href"].endswith("/artifacts/1/display-clone.pptx")
    assert body["artifacts"][1]["href"].endswith("/artifacts/1/editable-rebuild.pptx")
