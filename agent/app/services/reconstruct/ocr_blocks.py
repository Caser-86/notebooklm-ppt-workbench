def normalize_ocr_blocks(raw_blocks: list[dict]) -> list[dict]:
    normalized = []
    for block in raw_blocks:
        normalized.append(
            {
                "text": block["text"].strip(),
                "x": float(block["x"]),
                "y": float(block["y"]),
                "width": float(block["width"]),
                "height": float(block["height"]),
                "font_size": float(block.get("font_size", 18)),
            }
        )
    return normalized
