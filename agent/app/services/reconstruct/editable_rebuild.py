from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
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


def set_table_cell_borders(cell, color: str = "A8B3C7", width: str = "12700") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    for border_name in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        existing = tc_pr.find(qn(border_name))
        if existing is not None:
            tc_pr.remove(existing)

        border = OxmlElement(border_name)
        border.set("w", width)
        solid_fill = OxmlElement("a:solidFill")
        srgb = OxmlElement("a:srgbClr")
        srgb.set("val", color)
        solid_fill.append(srgb)
        border.append(solid_fill)
        preset_dash = OxmlElement("a:prstDash")
        preset_dash.set("val", "solid")
        border.append(preset_dash)
        round_join = OxmlElement("a:round")
        border.append(round_join)
        head_end = OxmlElement("a:headEnd")
        head_end.set("type", "none")
        head_end.set("w", "med")
        head_end.set("len", "med")
        border.append(head_end)
        tail_end = OxmlElement("a:tailEnd")
        tail_end.set("type", "none")
        tail_end.set("w", "med")
        tail_end.set("len", "med")
        border.append(tail_end)
        tc_pr.append(border)


def style_table_cell(cell, is_header: bool) -> None:
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0xE9, 0xEE, 0xF7) if is_header else RGBColor(0xFF, 0xFF, 0xFF)
    set_table_cell_borders(cell)


def build_editable_rebuild(raw_blocks: list[dict], output_path: Path) -> Path:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    for slide_blocks in analyze_rebuild_layout(raw_blocks):
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        for block in slide_blocks:
            left, top, width, height = resolve_render_geometry(block)
            if block.get("content_type") == "table":
                table_shape = slide.shapes.add_table(
                    block["rows"],
                    block["cols"],
                    Inches(left),
                    Inches(top),
                    Inches(width),
                    Inches(height),
                )
                table = table_shape.table
                for column_index, column_width in enumerate(block.get("column_widths", [])):
                    table.columns[column_index].width = Inches(column_width)
                for row_index, row_cells in enumerate(block["cells"]):
                    for column_index, cell_data in enumerate(row_cells):
                        if cell_data.get("merged"):
                            continue
                        cell = table.cell(row_index, column_index)
                        colspan = int(cell_data.get("colspan", 1))
                        if colspan > 1:
                            cell.merge(table.cell(row_index, column_index + colspan - 1))
                        style_table_cell(cell, is_header=row_index == 0)
                        text_frame = cell.text_frame
                        text_frame.clear()
                        paragraph = text_frame.paragraphs[0]
                        run = paragraph.add_run()
                        run.text = cell_data["text"]
                        run.font.size = Pt(cell_data.get("font_size", 18))
                        run.font.bold = row_index == 0
                continue

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
