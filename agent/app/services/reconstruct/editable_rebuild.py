from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from app.services.reconstruct.layout_analysis import analyze_rebuild_layout


def resolve_render_geometry(block: dict) -> tuple[float, float, float, float]:
    left = block["x"]
    top = block["y"]
    width = block["width"]
    height = block["height"]

    if block.get("text_role") in {"body", "list_item", "caption"}:
        column_index = block.get("column_index")
        if column_index == 0:
            width = min(width, 5.1)
        elif column_index == 1:
            left = max(left, 6.8)
            width = min(width, 5.1)

    return left, top, width, height


def build_editable_rebuild(raw_blocks: list[dict], output_path: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    for slide_blocks in analyze_rebuild_layout(raw_blocks):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        for block in slide_blocks:
            left, top, width, height = resolve_render_geometry(block)
            if block.get("content_type") == "image":
                image_path = Path(block["image_path"])
                slide.shapes.add_picture(
                    str(image_path),
                    left=Inches(left),
                    top=Inches(top),
                    width=Inches(width),
                    height=Inches(height),
                )
                continue

            textbox = slide.shapes.add_textbox(
                left=Inches(left),
                top=Inches(top),
                width=Inches(width),
                height=Inches(height),
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
                run.font.italic = paragraph_block.get("text_role") == "caption"

    presentation.save(output_path)
    return output_path
