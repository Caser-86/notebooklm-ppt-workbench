def normalize_ocr_blocks(raw_blocks: list[dict]) -> list[dict]:
    normalized = []
    for block in raw_blocks:
        normalized.append(
            {
                "text": block["text"].strip(),
                "slide_index": int(block.get("slide_index", 0)),
                "x": float(block["x"]),
                "y": float(block["y"]),
                "width": float(block["width"]),
                "height": float(block["height"]),
                "font_size": float(block.get("font_size", 18)),
            }
        )
    return normalized


def group_ocr_blocks_by_slide_lines(raw_blocks: list[dict], y_threshold: float = 0.12) -> list[list[dict]]:
    normalized = normalize_ocr_blocks(raw_blocks)
    if not normalized:
        return []

    grouped_by_slide: dict[int, list[dict]] = {}
    for block in sorted(normalized, key=lambda item: (item["slide_index"], item["y"], item["x"])):
        grouped_by_slide.setdefault(block["slide_index"], []).append(block)

    slide_lines: list[list[dict]] = []
    for slide_index in sorted(grouped_by_slide):
        lines: list[dict] = []
        current_line: dict | None = None

        for block in grouped_by_slide[slide_index]:
            if current_line is None or abs(block["y"] - current_line["y"]) > y_threshold:
                current_line = {
                    "slide_index": slide_index,
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
                line["text_role"] = "title" if slide_max_font >= 24 and line["font_size"] == slide_max_font else "body"

        slide_lines.append(lines)

    return slide_lines
