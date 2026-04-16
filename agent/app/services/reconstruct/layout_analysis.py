from app.services.reconstruct.ocr_blocks import group_ocr_blocks_by_slide_lines


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
        analyzed_slides.append(merge_consecutive_text_blocks(apply_vertical_spacing(slide_blocks)))

    return analyzed_slides
