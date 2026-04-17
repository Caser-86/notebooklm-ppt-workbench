from app.services.reconstruct.ocr_blocks import group_ocr_blocks_by_slide_lines


def _cluster_positions(values: list[float], threshold: float) -> list[float]:
    clusters: list[float] = []
    for value in sorted(values):
        if not clusters or abs(value - clusters[-1]) > threshold:
            clusters.append(value)
    return clusters


def detect_table_blocks(slide_blocks: list[dict]) -> list[dict]:
    body_blocks = [
        block for block in slide_blocks
        if block.get("text_role") == "body" and block.get("content_type") == "text"
    ]
    if len(body_blocks) < 4:
        return slide_blocks

    row_positions = _cluster_positions([block["y"] for block in body_blocks], 0.25)
    column_positions = _cluster_positions([block["x"] for block in body_blocks], 0.5)
    if len(row_positions) < 2 or len(column_positions) < 2:
        return slide_blocks

    base_column_widths = [
        max(
            (
                block["width"]
                for block in body_blocks
                if min(range(len(column_positions)), key=lambda index: abs(block["x"] - column_positions[index])) == column_index
            ),
            default=1.0,
        )
        for column_index in range(len(column_positions))
    ]

    grid: dict[tuple[int, int], dict] = {}
    for block in body_blocks:
        row_index = min(range(len(row_positions)), key=lambda index: abs(block["y"] - row_positions[index]))
        column_index = min(range(len(column_positions)), key=lambda index: abs(block["x"] - column_positions[index]))
        block_right = block["x"] + block["width"]
        block_bottom = block["y"] + block["height"]
        colspan = 1
        for next_column in range(column_index + 1, len(column_positions)):
            if block_right >= column_positions[next_column] + 0.25:
                colspan += 1
            else:
                break
        rowspan = 1
        max_rowspan_rows = 3
        for next_row in range(row_index + 1, min(len(row_positions), row_index + max_rowspan_rows)):
                if block_bottom >= row_positions[next_row] + 0.15:
                    rowspan += 1
                else:
                    break

        grid_key = (row_index, column_index)
        if grid_key in grid:
            return slide_blocks

        grid[grid_key] = {
            "text": block["text"],
            "font_size": block["font_size"],
            "colspan": colspan,
            "rowspan": rowspan,
        }
        for covered_row in range(row_index, row_index + rowspan):
            for covered_column in range(column_index, column_index + colspan):
                if covered_row == row_index and covered_column == column_index:
                    continue
                merged_key = (covered_row, covered_column)
                if merged_key in grid:
                    return slide_blocks
                grid[merged_key] = {"merged": True}

    expected_slots = len(row_positions) * len(column_positions)
    if len(grid) != expected_slots:
        return slide_blocks

    table_cells = [
        [
            grid[(row_index, column_index)]
            for column_index in range(len(column_positions))
        ]
        for row_index in range(len(row_positions))
    ]
    column_widths = [
        base_column_widths[column_index]
        for column_index in range(len(column_positions))
    ]
    first_row_has_group_header = any(
        (cell.get("colspan", 1) > 1)
        for cell in table_cells[0]
        if not cell.get("merged")
    )
    header_rows = 2 if first_row_has_group_header and len(row_positions) > 2 else 1

    table_block = {
        "slide_index": body_blocks[0]["slide_index"],
        "content_type": "table",
        "text_role": "table",
        "text": "",
        "x": min(block["x"] for block in body_blocks),
        "y": min(block["y"] for block in body_blocks),
        "width": max(block["x"] + block["width"] for block in body_blocks) - min(block["x"] for block in body_blocks),
        "height": max(block["y"] + block["height"] for block in body_blocks) - min(block["y"] for block in body_blocks),
        "rows": len(row_positions),
        "cols": len(column_positions),
        "cells": table_cells,
        "column_widths": column_widths,
        "header_rows": header_rows,
    }

    remaining_blocks = [block for block in slide_blocks if block not in body_blocks]
    return sorted(remaining_blocks + [table_block], key=lambda item: (item["y"], item["x"]))


def classify_captions(slide_blocks: list[dict]) -> list[dict]:
    classified_blocks: list[dict] = []
    image_blocks = [block for block in slide_blocks if block["text_role"] == "image"]

    for block in slide_blocks:
        adjusted = dict(block)
        if adjusted["text_role"] == "body":
            for image in image_blocks:
                near_image_bottom = image["y"] + image["height"] <= adjusted["y"] <= image["y"] + image["height"] + 0.55
                overlaps_image_width = adjusted["x"] < image["x"] + image["width"] and adjusted["x"] + adjusted["width"] > image["x"]
                if adjusted["font_size"] <= 14 and near_image_bottom and overlaps_image_width:
                    adjusted["text_role"] = "caption"
                    adjusted["x"] = image["x"]
                    adjusted["width"] = min(adjusted["width"], image["width"])
                    break

        classified_blocks.append(adjusted)

    return classified_blocks


def assign_column_indices(slide_blocks: list[dict]) -> list[dict]:
    indexed_blocks: list[dict] = []
    column_starts: list[float] = []

    for block in slide_blocks:
        adjusted = dict(block)
        if adjusted["text_role"] in {"body", "list_item", "caption"}:
            matched_index = None
            for index, start in enumerate(column_starts):
                if abs(adjusted["x"] - start) <= 0.5:
                    matched_index = index
                    break
            if matched_index is None:
                column_starts.append(adjusted["x"])
                column_starts.sort()
                matched_index = column_starts.index(adjusted["x"])
            adjusted["column_index"] = matched_index

        indexed_blocks.append(adjusted)

    return indexed_blocks


def apply_vertical_spacing(slide_blocks: list[dict]) -> list[dict]:
    adjusted_blocks: list[dict] = []
    active_list_indent: float | None = None
    image_blocks: list[dict] = []

    for block in slide_blocks:
        adjusted = dict(block)
        if adjusted["text_role"] == "image":
            image_blocks.append(adjusted)
            active_list_indent = None
        elif adjusted["text_role"] == "list_item":
            if active_list_indent is None:
                active_list_indent = adjusted["x"]
            adjusted["x"] = active_list_indent
            adjusted["width"] = min(adjusted["width"], 8.2 - adjusted["x"])
        elif adjusted["text_role"] == "body":
            adjusted["width"] = min(adjusted["width"], 8.2)
            active_list_indent = None
        else:
            active_list_indent = None

        if adjusted["text_role"] in {"body", "list_item"}:
            for image in image_blocks:
                vertical_overlap = adjusted["y"] < image["y"] + image["height"] and adjusted["y"] + adjusted["height"] > image["y"]
                horizontal_overlap = adjusted["x"] < image["x"] + image["width"] and adjusted["x"] + adjusted["width"] > image["x"]
                if vertical_overlap and horizontal_overlap and adjusted["x"] < image["x"]:
                    adjusted["width"] = min(adjusted["width"], max(0.6, image["x"] - adjusted["x"] - 0.08))

        if adjusted_blocks:
            previous = adjusted_blocks[-1]
            if previous["text_role"] == "image" and adjusted["text_role"] in {"body", "list_item"}:
                min_gap = 0.12
            elif previous["text_role"] == "title" and adjusted["text_role"] != "title":
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


def analyze_rebuild_layout(raw_blocks: list[dict]) -> list[list[dict]]:
    analyzed_slides: list[list[dict]] = []

    for slide_blocks in group_ocr_blocks_by_slide_lines(raw_blocks):
        analyzed_slides.append(
            assign_column_indices(
                merge_consecutive_text_blocks(
                    apply_vertical_spacing(
                        detect_table_blocks(
                            classify_captions(slide_blocks)
                        )
                    )
                )
            )
        )

    return analyzed_slides
