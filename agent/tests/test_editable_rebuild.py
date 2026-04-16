import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

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


def test_build_editable_rebuild_turns_bullet_lines_into_indented_list_items(tmp_path):
    blocks = [
        {"text": "Plan", "slide_index": 0, "x": 1, "y": 0.8, "width": 3.4, "height": 0.6, "font_size": 28},
        {"text": "- First checkpoint", "slide_index": 0, "x": 1.2, "y": 2.0, "width": 4.2, "height": 0.45, "font_size": 18},
    ]
    output_path = tmp_path / "editable-rebuild-list.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    shapes_with_text = [shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]

    list_paragraph = shapes_with_text[1].text_frame.paragraphs[0]

    assert list_paragraph.level == 1
    assert list_paragraph.runs[0].text == "First checkpoint"


def test_build_editable_rebuild_preserves_space_below_titles(tmp_path):
    blocks = [
        {"text": "Growth plan", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.2, "height": 0.7, "font_size": 30},
        {"text": "Body text begins too close in the OCR output.", "slide_index": 0, "x": 1, "y": 1.0, "width": 6, "height": 0.45, "font_size": 18},
    ]
    output_path = tmp_path / "editable-rebuild-spacing.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    shapes_with_text = [shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]
    title_shape = shapes_with_text[0]
    body_shape = shapes_with_text[1]

    assert body_shape.top >= title_shape.top + title_shape.height + Inches(0.18)


def test_build_editable_rebuild_keeps_consecutive_list_items_on_same_indent(tmp_path):
    blocks = [
        {"text": "Checklist", "slide_index": 0, "x": 1, "y": 0.8, "width": 3.4, "height": 0.6, "font_size": 28},
        {"text": "- First item", "slide_index": 0, "x": 1.2, "y": 2.0, "width": 4.2, "height": 0.45, "font_size": 18},
        {"text": "- Second item", "slide_index": 0, "x": 1.48, "y": 2.46, "width": 4.0, "height": 0.45, "font_size": 18},
    ]
    output_path = tmp_path / "editable-rebuild-list-indent.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    shapes_with_text = [shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]
    list_shape = shapes_with_text[1]
    list_paragraphs = [paragraph for paragraph in list_shape.text_frame.paragraphs if paragraph.text.strip()]

    assert len(shapes_with_text) == 2
    assert [paragraph.level for paragraph in list_paragraphs] == [1, 1]


def test_build_editable_rebuild_caps_body_width_for_readability(tmp_path):
    blocks = [
        {"text": "Body heading", "slide_index": 0, "x": 1, "y": 0.8, "width": 3.5, "height": 0.6, "font_size": 28},
        {
            "text": "A very wide paragraph should be narrowed to a more readable text column in the rebuilt slide.",
            "slide_index": 0,
            "x": 1,
            "y": 2.0,
            "width": 10.5,
            "height": 0.6,
            "font_size": 18,
        },
    ]
    output_path = tmp_path / "editable-rebuild-body-width.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    shapes_with_text = [shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]
    body_shape = shapes_with_text[1]

    assert body_shape.width <= Inches(8.2)


def test_build_editable_rebuild_merges_consecutive_body_blocks_into_one_text_frame(tmp_path):
    blocks = [
        {"text": "Expansion update", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.2, "height": 0.7, "font_size": 30},
        {"text": "We launched three pilots in Southeast Asia.", "slide_index": 0, "x": 1, "y": 2.0, "width": 6.1, "height": 0.45, "font_size": 18},
        {"text": "Each pilot now has local distribution support.", "slide_index": 0, "x": 1.02, "y": 2.55, "width": 6.0, "height": 0.45, "font_size": 18},
    ]
    output_path = tmp_path / "editable-rebuild-body-paragraphs.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    shapes_with_text = [shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]
    body_shape = shapes_with_text[1]
    body_paragraphs = [paragraph.text for paragraph in body_shape.text_frame.paragraphs if paragraph.text.strip()]

    assert len(shapes_with_text) == 2
    assert body_paragraphs == [
        "We launched three pilots in Southeast Asia.",
        "Each pilot now has local distribution support.",
    ]


def test_build_editable_rebuild_merges_consecutive_list_items_into_one_text_frame(tmp_path):
    blocks = [
        {"text": "Execution plan", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.2, "height": 0.7, "font_size": 30},
        {"text": "- Confirm export", "slide_index": 0, "x": 1.2, "y": 2.0, "width": 4.2, "height": 0.45, "font_size": 18},
        {"text": "- Trigger rebuild", "slide_index": 0, "x": 1.44, "y": 2.5, "width": 4.0, "height": 0.45, "font_size": 18},
    ]
    output_path = tmp_path / "editable-rebuild-list-paragraphs.pptx"

    build_editable_rebuild(blocks, output_path)

    presentation = Presentation(output_path)
    shapes_with_text = [shape for shape in presentation.slides[0].shapes if hasattr(shape, "text") and shape.text.strip()]
    list_shape = shapes_with_text[1]
    list_paragraphs = [paragraph for paragraph in list_shape.text_frame.paragraphs if paragraph.text.strip()]

    assert len(shapes_with_text) == 2
    assert [paragraph.text for paragraph in list_paragraphs] == ["Confirm export", "Trigger rebuild"]
    assert [paragraph.level for paragraph in list_paragraphs] == [1, 1]
