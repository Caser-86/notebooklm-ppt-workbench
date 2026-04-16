from app.services.reconstruct.ocr_blocks import group_ocr_blocks_by_slide_lines


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
        analyzed_slides.append(assign_column_indices(merge_consecutive_text_blocks(classify_captions(apply_vertical_spacing(slide_blocks)))))

    return analyzed_slides
