from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

from app.services.reconstruct.ocr_blocks import normalize_ocr_blocks


def build_editable_rebuild(raw_blocks: list[dict], output_path: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    for block in normalize_ocr_blocks(raw_blocks):
        textbox = slide.shapes.add_textbox(
            left=Inches(block["x"]),
            top=Inches(block["y"]),
            width=Inches(block["width"]),
            height=Inches(block["height"]),
        )
        paragraph = textbox.text_frame.paragraphs[0]
        paragraph.text = block["text"]
        paragraph.font.size = Pt(block["font_size"])

    if presentation.slides:
        first = presentation.slides._sldIdLst[0]
        presentation.slides._sldIdLst.remove(first)

    presentation.save(output_path)
    return output_path
