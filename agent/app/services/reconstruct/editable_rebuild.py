from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from app.services.reconstruct.layout_analysis import analyze_rebuild_layout


def build_editable_rebuild(raw_blocks: list[dict], output_path: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    for slide_blocks in analyze_rebuild_layout(raw_blocks):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        for block in slide_blocks:
            if block.get("content_type") == "image":
                image_path = Path(block["image_path"])
                slide.shapes.add_picture(
                    str(image_path),
                    left=Inches(block["x"]),
                    top=Inches(block["y"]),
                    width=Inches(block["width"]),
                    height=Inches(block["height"]),
                )
                continue

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
