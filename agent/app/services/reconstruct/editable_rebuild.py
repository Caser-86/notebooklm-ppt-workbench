from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from app.services.reconstruct.ocr_blocks import group_ocr_blocks_by_slide_lines


def build_editable_rebuild(raw_blocks: list[dict], output_path: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    for slide_blocks in group_ocr_blocks_by_slide_lines(raw_blocks):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        for block in slide_blocks:
            textbox = slide.shapes.add_textbox(
                left=Inches(block["x"]),
                top=Inches(block["y"]),
                width=Inches(block["width"]),
                height=Inches(block["height"]),
            )
            paragraph = textbox.text_frame.paragraphs[0]
            run = paragraph.add_run()
            run.text = block["text"]
            run.font.size = Pt(block["font_size"])
            run.font.bold = block.get("text_role") == "title"

    presentation.save(output_path)
    return output_path
