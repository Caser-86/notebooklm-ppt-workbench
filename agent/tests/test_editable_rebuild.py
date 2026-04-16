import json
from pathlib import Path

from app.services.reconstruct.editable_rebuild import build_editable_rebuild


def test_build_editable_rebuild_creates_text_boxes_from_ocr_blocks(tmp_path):
    blocks = json.loads(Path("tests/fixtures/ocr_blocks.json").read_text(encoding="utf-8"))
    output_path = tmp_path / "editable-rebuild.pptx"

    build_editable_rebuild(blocks, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0
