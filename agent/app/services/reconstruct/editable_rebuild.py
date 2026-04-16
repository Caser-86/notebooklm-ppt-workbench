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


def merge_consecutive_text_blocks(slide_blocks: list[dict]) -> list[dict]:
    merged_blocks: list[dict] = []

    for block in slide_blocks:
        current = dict(block)
        current["paragraphs"] = [dict(block)]

        if merged_blocks:
            previous = merged_blocks[-1]
            same_text_flow = (
                previous["text_role"] in {"body", "list_item"}
                and current["text_role"] == previous["text_role"]
                and abs(previous["x"] - current["x"]) <= 0.12
                and abs(previous["width"] - current["width"]) <= 0.6
                and abs(previous["font_size"] - current["font_size"]) <= 1.0
            )
            if same_text_flow:
                previous["paragraphs"].append(dict(block))
                bottom_edge = max(previous["y"] + previous["height"], current["y"] + current["height"])
                previous["height"] = bottom_edge - previous["y"]
                previous["width"] = max(previous["width"], current["width"])
                continue

        merged_blocks.append(current)

    return merged_blocks


def build_editable_rebuild(raw_blocks: list[dict], output_path: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    for slide_blocks in group_ocr_blocks_by_slide_lines(raw_blocks):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        for block in merge_consecutive_text_blocks(apply_vertical_spacing(slide_blocks)):
            textbox = slide.shapes.add_textbox(
                left=Inches(block["x"]),
                top=Inches(block["y"]),
                width=Inches(block["width"]),
                height=Inches(block["height"]),
            )
            text_frame = textbox.text_frame
            text_frame.clear()

            paragraphs = block.get("paragraphs", [block])
            for index, paragraph_block in enumerate(paragraphs):
                paragraph = text_frame.paragraphs[0] if index == 0 else text_frame.add_paragraph()
                paragraph.level = 1 if paragraph_block.get("text_role") == "list_item" else 0
                run = paragraph.add_run()
                run.text = paragraph_block["text"]
                run.font.size = Pt(paragraph_block["font_size"])
                run.font.bold = paragraph_block.get("text_role") == "title"

    presentation.save(output_path)
    return output_path
