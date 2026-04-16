from pathlib import Path

from app.services.crawler import extract_page_summary
from app.services.source_ingest import build_source_bundle


def test_extract_page_summary_from_fixture():
    html = Path("tests/fixtures/example_page.html").read_text(encoding="utf-8")
    summary = extract_page_summary("https://example.com", html)

    assert summary["title"] == "Example Launch"
    assert "Key metrics" in summary["content"]


def test_build_source_bundle_combines_prompt_links_and_files(tmp_path):
    file_path = tmp_path / "brief.txt"
    file_path.write_text("Launch plan for Q4", encoding="utf-8")

    bundle = build_source_bundle(
        prompt="Create an investor update",
        urls=["https://example.com"],
        file_paths=[file_path],
        image_paths=[],
        audio_paths=[],
        video_paths=[],
    )

    assert bundle.prompt == "Create an investor update"
    assert bundle.urls == ["https://example.com"]
    assert bundle.file_texts[0]["text"] == "Launch plan for Q4"
