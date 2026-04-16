from pathlib import Path

from app.services.reconstruct.display_clone import build_display_clone


def test_build_display_clone_creates_pptx_for_each_slide(tmp_path):
    slide_paths = [
        Path("tests/fixtures/slides/slide-1.png"),
        Path("tests/fixtures/slides/slide-2.png"),
    ]

    output_path = tmp_path / "display-clone.pptx"
    build_display_clone(slide_paths, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0
