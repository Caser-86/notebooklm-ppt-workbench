import json
from pathlib import Path

from pptx import Presentation

from app.services.reconstruct.editable_rebuild import build_editable_rebuild


def test_build_editable_rebuild_creates_text_boxes_from_ocr_blocks(tmp_path):
    blocks = json.loads(Path("tests/fixtures/ocr_blocks.json").read_text(encoding="utf-8"))
    output_path = tmp_path / "editable-rebuild.pptx"

    build_editable_rebuild(blocks, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_build_editable_rebuild_creates_multiple_slides_and_groups_same_line_blocks(tmp_path):
    blocks = [
        {"text": "Quarterly", "slide_index": 0, "x": 1, "y": 1, "width": 1.6, "height": 0.5, "font_size": 24},
        {"text": "update", "slide_index": 0, "x": 2.7, "y": 1.02, "width": 1.6, "height": 0.5, "font_size": 24},
        {"text": "Revenue", "slide_index": 1, "x": 1, "y": 1, "width": 1.6, "height": 0.5, "font_size": 22},
        {"text": "22%", "slide_index": 1, "x": 2.8, "y": 1.01, "width": 1.2, "height": 0.5, "font_size": 22},
    ]
    output_path = tmp_path / "editable-rebuild-multi.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    slide_texts = [
        [shape.text for shape in slide.shapes if hasattr(shape, "text") and shape.text.strip()]
        for slide in presentation.slides
    ]

    assert len(presentation.slides) == 2
    assert slide_texts[0] == ["Quarterly update"]
    assert slide_texts[1] == ["Revenue 22%"]


def test_build_editable_rebuild_marks_title_blocks_as_bolder_than_body(tmp_path):
    blocks = [
        {"text": "Market expansion", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.5, "height": 0.7, "font_size": 30},
        {"text": "We entered three new regions this quarter.", "slide_index": 0, "x": 1, "y": 2.1, "width": 6.2, "height": 0.6, "font_size": 18},
    ]
    output_path = tmp_path / "editable-rebuild-title-body.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    shapes_with_text = [shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]

    title_run = shapes_with_text[0].text_frame.paragraphs[0].runs[0]
    body_run = shapes_with_text[1].text_frame.paragraphs[0].runs[0]

    assert title_run.text == "Market expansion"
    assert title_run.font.bold is True
    assert body_run.font.bold in (None, False)
    assert title_run.font.size.pt > body_run.font.size.pt
