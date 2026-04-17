def _strip_list_marker(text: str) -> str:
    for prefix in ("- ", "• ", "* ", "· "):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def _is_list_item_text(text: str) -> bool:
    return _strip_list_marker(text) != text


def _cluster_positions(values: list[float], threshold: float) -> list[float]:
    clusters: list[float] = []
    for value in sorted(values):
        if not clusters or abs(value - clusters[-1]) > threshold:
            clusters.append(value)
    return clusters


def normalize_ocr_blocks(raw_blocks: list[dict]) -> list[dict]:
    normalized = []
    for block in raw_blocks:
        normalized.append(
            {
                "text": block["text"].strip(),
                "slide_index": int(block.get("slide_index", 0)),
                "content_type": block.get("content_type", "text"),
                "image_path": block.get("image_path"),
                "x": float(block["x"]),
                "y": float(block["y"]),
                "width": float(block["width"]),
                "height": float(block["height"]),
                "font_size": float(block.get("font_size", 18)),
            }
        )
    return normalized


def group_raw_ocr_blocks_by_slide(raw_blocks: list[dict]) -> list[list[dict]]:
    normalized = normalize_ocr_blocks(raw_blocks)
    if not normalized:
        return []

    grouped_by_slide: dict[int, list[dict]] = {}
    for block in sorted(normalized, key=lambda item: (item["slide_index"], item["y"], item["x"])):
        grouped_by_slide.setdefault(block["slide_index"], []).append(block)

    grouped_slides: list[list[dict]] = []
    for slide_index in sorted(grouped_by_slide):
        slide_blocks = grouped_by_slide[slide_index]
        text_blocks = [block for block in slide_blocks if block.get("content_type") != "image"]
        image_blocks = [
            {
                **block,
                "text_role": "image",
            }
            for block in slide_blocks
            if block.get("content_type") == "image"
        ]

        if text_blocks:
            slide_max_font = max(block["font_size"] for block in text_blocks)
            classified_text_blocks = []
            for block in text_blocks:
                adjusted = dict(block)
                if slide_max_font >= 24 and adjusted["font_size"] == slide_max_font and not _is_list_item_text(adjusted["text"]):
                    adjusted["text_role"] = "title"
                elif _is_list_item_text(adjusted["text"]):
                    adjusted["text_role"] = "list_item"
                    adjusted["text"] = _strip_list_marker(adjusted["text"])
                else:
                    adjusted["text_role"] = "body"
                classified_text_blocks.append(adjusted)
        else:
            classified_text_blocks = []

        grouped_slides.append(sorted(classified_text_blocks + image_blocks, key=lambda item: (item["y"], item["x"])))

    return grouped_slides


def group_ocr_blocks_by_slide_lines(raw_blocks: list[dict], y_threshold: float = 0.12) -> list[list[dict]]:
    normalized = normalize_ocr_blocks(raw_blocks)
    if not normalized:
        return []

    grouped_by_slide: dict[int, list[dict]] = {}
    for block in sorted(normalized, key=lambda item: (item["slide_index"], item["y"], item["x"])):
        grouped_by_slide.setdefault(block["slide_index"], []).append(block)

    slide_lines: list[list[dict]] = []
    for slide_index in sorted(grouped_by_slide):
        slide_blocks = sorted(
            grouped_by_slide[slide_index],
            key=lambda block: (
                round(block["y"] / max(y_threshold * 2, 0.01)),
                block["x"],
                block["y"],
            ),
        )
        text_blocks = [block for block in slide_blocks if block.get("content_type") != "image"]
        row_starts = _cluster_positions([block["y"] for block in text_blocks], y_threshold)
        row_block_counts = {row_index: 0 for row_index in range(len(row_starts))}
        for block in text_blocks:
            row_index = min(range(len(row_starts)), key=lambda index: abs(block["y"] - row_starts[index]))
            row_block_counts[row_index] += 1
        table_like_rows = {
            row_index
            for row_index, count in row_block_counts.items()
            if count >= 3 and sum(1 for other_count in row_block_counts.values() if other_count >= 3) >= 2
        }
        image_blocks = [
            {
                **block,
                "text_role": "image",
            }
            for block in slide_blocks
            if block.get("content_type") == "image"
        ]

        lines: list[dict] = []
        current_line: dict | None = None

        for block in slide_blocks:
            if block.get("content_type") == "image":
                continue
            row_index = min(range(len(row_starts)), key=lambda index: abs(block["y"] - row_starts[index])) if row_starts else 0
            horizontal_gap = (
                None
                if current_line is None
                else block["x"] - (current_line["x"] + current_line["width"])
            )
            same_line_and_close = (
                current_line is not None
                and row_index not in table_like_rows
                and abs(block["y"] - current_line["y"]) <= y_threshold
                and horizontal_gap is not None
                and horizontal_gap <= 0.25
                and (block["x"] - current_line["x"]) <= 4.5
            )
            if not same_line_and_close:
                current_line = {
                    "slide_index": slide_index,
                    "content_type": "text",
                    "image_path": None,
                    "text": block["text"],
                    "x": block["x"],
                    "y": block["y"],
                    "width": block["width"],
                    "height": block["height"],
                    "font_size": block["font_size"],
                }
                lines.append(current_line)
                continue

            current_line["text"] = f'{current_line["text"]} {block["text"]}'.strip()
            current_line["x"] = min(current_line["x"], block["x"])
            right_edge = max(current_line["x"] + current_line["width"], block["x"] + block["width"])
            current_line["width"] = right_edge - current_line["x"]
            current_line["height"] = max(current_line["height"], block["height"])
            current_line["font_size"] = max(current_line["font_size"], block["font_size"])

        if lines:
            slide_max_font = max(line["font_size"] for line in lines)
            for line in lines:
                if slide_max_font >= 24 and line["font_size"] == slide_max_font and not _is_list_item_text(line["text"]):
                    line["text_role"] = "title"
                elif _is_list_item_text(line["text"]):
                    line["text_role"] = "list_item"
                    line["text"] = _strip_list_marker(line["text"])
                else:
                    line["text_role"] = "body"

        slide_lines.append(sorted(lines + image_blocks, key=lambda item: (item["y"], item["x"])))

    return slide_lines
