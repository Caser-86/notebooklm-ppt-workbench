from pathlib import Path

from app.services.reconstruct.display_clone import build_display_clone
from app.services.reconstruct.editable_rebuild import build_editable_rebuild


def test_export_handoff_supports_both_output_decks(tmp_path):
    slide_paths = [Path("tests/fixtures/slides/slide-1.png")]
    display_output = tmp_path / "display.pptx"
    editable_output = tmp_path / "editable.pptx"

    build_display_clone(slide_paths, display_output)
    build_editable_rebuild(
        [{"text": "Quarterly update", "x": 1, "y": 1, "width": 4, "height": 1, "font_size": 24}],
        editable_output,
    )

    assert display_output.exists()
    assert editable_output.exists()
