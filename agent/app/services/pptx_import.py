import base64
from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


PLACEHOLDER_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wn7Zp4AAAAASUVORK5CYII="
)
EMU_PER_INCH = 914400


@dataclass
class ImportedSlideBundle:
    slide_index: int
    preview_image_path: str
    text_dump: str
    structure_json_path: str
    blocks: list[dict]


@dataclass
class ImportedPresentationBundle:
    source_type: str
    page_count: int
    slides: list[ImportedSlideBundle]


def classify_pptx_source(pptx_path: Path) -> str:
    presentation = Presentation(pptx_path)
    texts = " ".join(_iter_slide_texts(presentation)).lower()
    if "editable rebuild" in texts or "display clone" in texts:
        return "internal_generated"
    if "notebooklm" in texts:
        return "notebooklm_export"
    return "generic_pptx"


def extract_pptx_assets(project_id: int, pptx_path: Path, import_dir: Path) -> ImportedPresentationBundle:
    del project_id  # project_id is reserved for future slide-specific asset strategies.
    presentation = Presentation(pptx_path)
    source_type = classify_pptx_source(pptx_path)
    slides: list[ImportedSlideBundle] = []

    for index, slide in enumerate(presentation.slides, start=1):
        blocks = _extract_text_blocks(slide, index)
        blocks.extend(_extract_picture_blocks(slide, index, import_dir))
        blocks.extend(_extract_table_blocks(slide, index))
        blocks.extend(_extract_chart_blocks(slide, index))
        blocks.extend(_extract_group_blocks(slide, index, import_dir))
        blocks = _group_imported_icon_cards(blocks)
        text_dump = "\n".join(
            shape.text.strip()
            for shape in slide.shapes
            if hasattr(shape, "text") and shape.text and shape.text.strip()
        )
        preview_path = import_dir / f"slide-{index}.png"
        preview_path.write_bytes(PLACEHOLDER_PNG_BYTES)
        slides.append(
            ImportedSlideBundle(
                slide_index=index,
                preview_image_path=str(preview_path),
                text_dump=text_dump,
                structure_json_path="",
                blocks=blocks,
            )
        )

    return ImportedPresentationBundle(source_type=source_type, page_count=len(slides), slides=slides)


def _iter_slide_texts(presentation: Presentation) -> list[str]:
    texts: list[str] = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                texts.append(shape.text)
    return texts


def _extract_text_blocks(slide, slide_index: int) -> list[dict]:
    blocks: list[dict] = []
    title_shape = getattr(slide.shapes, "title", None)

    for shape in slide.shapes:
        if not hasattr(shape, "text") or not shape.text or not shape.text.strip():
            continue

        run_font = None
        if getattr(shape, "text_frame", None) and shape.text_frame.paragraphs:
            first_paragraph = shape.text_frame.paragraphs[0]
            if first_paragraph.runs:
                run_font = first_paragraph.runs[0].font

        blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_text",
                "text": shape.text.strip(),
                "text_role": "title" if title_shape is not None and shape == title_shape else "body",
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "font_size": (run_font.size.pt if run_font and run_font.size else 24),
                "bold": bool(run_font.bold) if run_font and run_font.bold is not None else False,
                "italic": bool(run_font.italic) if run_font and run_font.italic is not None else False,
            }
        )

    return blocks


def _extract_picture_blocks(slide, slide_index: int, import_dir: Path) -> list[dict]:
    picture_blocks: list[dict] = []

    for picture_index, shape in enumerate(slide.shapes, start=1):
        if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
            continue

        suffix = Path(shape.image.filename or f"image-{picture_index}.png").suffix or ".png"
        image_path = import_dir / f"slide-{slide_index}-image-{picture_index}{suffix}"
        image_path.write_bytes(shape.image.blob)
        picture_blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_image",
                "image_path": str(image_path),
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
            }
        )

    return picture_blocks


def _extract_table_blocks(slide, slide_index: int) -> list[dict]:
    table_blocks: list[dict] = []

    for shape in slide.shapes:
        if not getattr(shape, "has_table", False):
            continue

        table = shape.table
        table_blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_table",
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "rows": len(table.rows),
                "cols": len(table.columns),
                "cells": [
                    [
                        {
                            "text": cell.text,
                            "font_size": 18,
                        }
                        for cell in row.cells
                    ]
                    for row in table.rows
                ],
                "column_widths": [column.width / EMU_PER_INCH for column in table.columns],
                "header_rows": 1,
            }
        )

    return table_blocks


def _extract_chart_blocks(slide, slide_index: int) -> list[dict]:
    chart_blocks: list[dict] = []

    for shape in slide.shapes:
        if not getattr(shape, "has_chart", False):
            continue

        chart = shape.chart
        title = ""
        if chart.has_title:
            title = chart.chart_title.text_frame.text

        categories = [category.label for category in chart.plots[0].categories]
        series = [
            {
                "name": series.name,
                "values": list(series.values),
            }
            for series in chart.series
        ]

        chart_blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "imported_chart",
                "chart_type": str(chart.chart_type),
                "title": title,
                "categories": categories,
                "series": series,
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "snapshot_path": "",
                "fallback_mode": "table",
            }
        )

    return chart_blocks


def _extract_group_blocks(slide, slide_index: int, import_dir: Path) -> list[dict]:
    group_blocks: list[dict] = []
    for shape in slide.shapes:
        if shape.shape_type != MSO_SHAPE_TYPE.GROUP:
            continue
        group_blocks.extend(_expand_group_shape(shape, slide_index, import_dir))
    return group_blocks


def _expand_group_shape(shape, slide_index: int, import_dir: Path) -> list[dict]:
    promoted_blocks: list[dict] = []
    unsupported_types: list[str] = []

    for child in shape.shapes:
        child_blocks = _extract_supported_group_child(child, slide_index, import_dir)
        if child_blocks:
            promoted_blocks.extend(child_blocks)
        else:
            unsupported_types.append(str(child.shape_type))

    if unsupported_types:
        promoted_blocks.append(
            {
                "slide_index": slide_index,
                "content_type": "unsupported_group",
                "x": shape.left / EMU_PER_INCH,
                "y": shape.top / EMU_PER_INCH,
                "width": shape.width / EMU_PER_INCH,
                "height": shape.height / EMU_PER_INCH,
                "supported_child_count": len(promoted_blocks),
                "unsupported_child_count": len(unsupported_types),
                "unsupported_types": unsupported_types,
                "fallback_mode": "text",
                "snapshot_path": "",
            }
        )

    return promoted_blocks


def _extract_supported_group_child(child, slide_index: int, import_dir: Path) -> list[dict]:
    if hasattr(child, "text") and child.text and child.text.strip():
        return [_normalize_text_shape(child, slide_index)]
    if child.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return [_normalize_picture_shape(child, slide_index, import_dir)]
    if getattr(child, "has_table", False):
        return [_normalize_table_shape(child, slide_index)]
    if getattr(child, "has_chart", False):
        return [_normalize_chart_shape(child, slide_index)]
    return []


def _normalize_text_shape(shape, slide_index: int) -> dict:
    run_font = None
    if getattr(shape, "text_frame", None) and shape.text_frame.paragraphs:
        first_paragraph = shape.text_frame.paragraphs[0]
        if first_paragraph.runs:
            run_font = first_paragraph.runs[0].font

    return {
        "slide_index": slide_index,
        "content_type": "imported_text",
        "text": shape.text.strip(),
        "text_role": "body",
        "x": shape.left / EMU_PER_INCH,
        "y": shape.top / EMU_PER_INCH,
        "width": shape.width / EMU_PER_INCH,
        "height": shape.height / EMU_PER_INCH,
        "font_size": (run_font.size.pt if run_font and run_font.size else 24),
        "bold": bool(run_font.bold) if run_font and run_font.bold is not None else False,
        "italic": bool(run_font.italic) if run_font and run_font.italic is not None else False,
    }


def _normalize_picture_shape(shape, slide_index: int, import_dir: Path) -> dict:
    suffix = Path(shape.image.filename or "group-image.png").suffix or ".png"
    image_path = import_dir / f"group-slide-{slide_index}-{shape.shape_id}{suffix}"
    image_path.write_bytes(shape.image.blob)
    return {
        "slide_index": slide_index,
        "content_type": "imported_image",
        "image_path": str(image_path),
        "x": shape.left / EMU_PER_INCH,
        "y": shape.top / EMU_PER_INCH,
        "width": shape.width / EMU_PER_INCH,
        "height": shape.height / EMU_PER_INCH,
    }


def _normalize_table_shape(shape, slide_index: int) -> dict:
    table = shape.table
    return {
        "slide_index": slide_index,
        "content_type": "imported_table",
        "x": shape.left / EMU_PER_INCH,
        "y": shape.top / EMU_PER_INCH,
        "width": shape.width / EMU_PER_INCH,
        "height": shape.height / EMU_PER_INCH,
        "rows": len(table.rows),
        "cols": len(table.columns),
        "cells": [
            [
                {"text": cell.text, "font_size": 18}
                for cell in row.cells
            ]
            for row in table.rows
        ],
        "column_widths": [column.width / EMU_PER_INCH for column in table.columns],
        "header_rows": 1,
    }


def _normalize_chart_shape(shape, slide_index: int) -> dict:
    chart = shape.chart
    title = chart.chart_title.text_frame.text if chart.has_title else ""
    categories = [category.label for category in chart.plots[0].categories]
    series = [{"name": item.name, "values": list(item.values)} for item in chart.series]
    return {
        "slide_index": slide_index,
        "content_type": "imported_chart",
        "chart_type": str(chart.chart_type),
        "title": title,
        "categories": categories,
        "series": series,
        "x": shape.left / EMU_PER_INCH,
        "y": shape.top / EMU_PER_INCH,
        "width": shape.width / EMU_PER_INCH,
        "height": shape.height / EMU_PER_INCH,
        "snapshot_path": "",
        "fallback_mode": "table",
    }


def _group_imported_icon_cards(blocks: list[dict]) -> list[dict]:
    image_blocks = [
        block for block in blocks
        if block.get("content_type") == "imported_image"
        and block.get("width", 0) <= 1.1
        and block.get("height", 0) <= 1.1
    ]
    text_blocks = [block for block in blocks if block.get("content_type") == "imported_text"]

    if not image_blocks or len(text_blocks) < 2:
        return blocks

    consumed_ids: set[int] = set()
    grouped_blocks: list[dict] = []

    for image in image_blocks:
        title_candidate = next(
            (
                block for block in text_blocks
                if id(block) not in consumed_ids
                and block.get("text_role") == "body"
                and image["x"] + image["width"] <= block["x"] <= image["x"] + image["width"] + 1.6
                and abs(block["y"] - image["y"]) <= 0.25
            ),
            None,
        )
        if title_candidate is None:
            continue

        body_candidate = next(
            (
                block for block in text_blocks
                if id(block) not in consumed_ids
                and block is not title_candidate
                and block.get("text_role") == "body"
                and block["x"] >= title_candidate["x"] - 0.1
                and block["y"] >= title_candidate["y"] + title_candidate["height"] - 0.05
                and block["y"] <= title_candidate["y"] + title_candidate["height"] + 0.9
            ),
            None,
        )
        if body_candidate is None:
            continue

        consumed_ids.add(id(title_candidate))
        consumed_ids.add(id(body_candidate))
        consumed_ids.add(id(image))
        grouped_blocks.append(
            {
                "slide_index": image["slide_index"],
                "content_type": "imported_icon_card",
                "x": min(image["x"], title_candidate["x"], body_candidate["x"]),
                "y": min(image["y"], title_candidate["y"], body_candidate["y"]),
                "width": max(
                    image["x"] + image["width"],
                    title_candidate["x"] + title_candidate["width"],
                    body_candidate["x"] + body_candidate["width"],
                ) - min(image["x"], title_candidate["x"], body_candidate["x"]),
                "height": max(
                    image["y"] + image["height"],
                    title_candidate["y"] + title_candidate["height"],
                    body_candidate["y"] + body_candidate["height"],
                ) - min(image["y"], title_candidate["y"], body_candidate["y"]),
                "icon_path": image["image_path"],
                "icon_x": image["x"],
                "icon_y": image["y"],
                "icon_width": image["width"],
                "icon_height": image["height"],
                "title_text": title_candidate["text"],
                "title_x": title_candidate["x"],
                "title_y": title_candidate["y"],
                "title_width": title_candidate["width"],
                "title_height": title_candidate["height"],
                "title_font_size": title_candidate.get("font_size", 20),
                "body_text": body_candidate["text"],
                "body_x": body_candidate["x"],
                "body_y": body_candidate["y"],
                "body_width": body_candidate["width"],
                "body_height": body_candidate["height"],
                "body_font_size": body_candidate.get("font_size", 16),
            }
        )

    if not grouped_blocks:
        return blocks

    remaining_blocks = [
        block for block in blocks
        if id(block) not in consumed_ids
    ]
    return sorted(remaining_blocks + grouped_blocks, key=lambda item: (item["y"], item["x"]))
