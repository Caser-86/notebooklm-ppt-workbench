from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from app.services.reconstruct.ocr_blocks import group_ocr_blocks_by_slide_lines


def apply_vertical_spacing(slide_blocks: list[dict]) -> list[dict]:
    adjusted_blocks: list[dict] = []
    active_list_indent: float | None = None

    for block in slide_blocks:
        adjusted = dict(block)
        if adjusted["text_role"] == "list_item":
            if active_list_indent is None:
                active_list_indent = adjusted["x"]
            adjusted["x"] = active_list_indent
            adjusted["width"] = min(adjusted["width"], 8.2 - adjusted["x"])
        elif adjusted["text_role"] == "body":
            adjusted["width"] = min(adjusted["width"], 8.2)
            active_list_indent = None
        else:
            active_list_indent = None

        if adjusted_blocks:
            previous = adjusted_blocks[-1]
            if previous["text_role"] == "title" and adjusted["text_role"] != "title":
                min_gap = 0.18
            elif adjusted["text_role"] == "list_item":
                min_gap = 0.08
            else:
                min_gap = 0.06

            adjusted["y"] = max(adjusted["y"], previous["y"] + previous["height"] + min_gap)

        adjusted_blocks.append(adjusted)

    return adjusted_blocks


def build_editable_rebuild(raw_blocks: list[dict], output_path: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    for slide_blocks in group_ocr_blocks_by_slide_lines(raw_blocks):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        for block in apply_vertical_spacing(slide_blocks):
            textbox = slide.shapes.add_textbox(
                left=Inches(block["x"]),
                top=Inches(block["y"]),
                width=Inches(block["width"]),
                height=Inches(block["height"]),
            )
            paragraph = textbox.text_frame.paragraphs[0]
            paragraph.level = 1 if block.get("text_role") == "list_item" else 0
            run = paragraph.add_run()
            run.text = block["text"]
            run.font.size = Pt(block["font_size"])
            run.font.bold = block.get("text_role") == "title"

    presentation.save(output_path)
    return output_path
