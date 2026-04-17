from app.services.reconstruct.layout_analysis import analyze_rebuild_layout


def test_analyze_rebuild_layout_merges_body_list_and_image_blocks_by_slide():
    blocks = [
        {"text": "Launch overview", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.2, "height": 0.7, "font_size": 30},
        {"text": "We opened three pilots this quarter.", "slide_index": 0, "x": 1, "y": 2.0, "width": 6.1, "height": 0.45, "font_size": 18},
        {"text": "Each pilot now has local support.", "slide_index": 0, "x": 1.02, "y": 2.55, "width": 6.0, "height": 0.45, "font_size": 18},
        {"text": "- Confirm export", "slide_index": 0, "x": 1.2, "y": 3.4, "width": 4.2, "height": 0.45, "font_size": 18},
        {"text": "- Trigger rebuild", "slide_index": 0, "x": 1.44, "y": 3.92, "width": 4.0, "height": 0.45, "font_size": 18},
        {
            "text": "",
            "slide_index": 0,
            "x": 7.2,
            "y": 1.9,
            "width": 4.0,
            "height": 2.6,
            "content_type": "image",
            "image_path": "tests/fixtures/slides/slide-1.png",
        },
        {"text": "Second slide title", "slide_index": 1, "x": 1, "y": 0.8, "width": 4.4, "height": 0.7, "font_size": 28},
    ]

    slides = analyze_rebuild_layout(blocks)

    assert len(slides) == 2
    first_slide = slides[0]
    second_slide = slides[1]

    assert [block["text_role"] for block in first_slide] == ["title", "image", "body", "list_item"]
    assert first_slide[2]["paragraphs"][0]["text"] == "We opened three pilots this quarter."
    assert first_slide[2]["paragraphs"][1]["text"] == "Each pilot now has local support."
    assert [paragraph["text"] for paragraph in first_slide[3]["paragraphs"]] == ["Confirm export", "Trigger rebuild"]
    assert first_slide[2]["x"] + first_slide[2]["width"] <= first_slide[1]["x"] - 0.08
    assert second_slide[0]["text"] == "Second slide title"


def test_analyze_rebuild_layout_marks_small_text_under_image_as_caption():
    blocks = [
        {"text": "Growth snapshot", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.2, "height": 0.7, "font_size": 30},
        {
            "text": "",
            "slide_index": 0,
            "x": 6.8,
            "y": 1.5,
            "width": 4.0,
            "height": 2.2,
            "content_type": "image",
            "image_path": "tests/fixtures/slides/slide-1.png",
        },
        {
            "text": "Pilot launch event, March 2026",
            "slide_index": 0,
            "x": 6.9,
            "y": 3.82,
            "width": 3.5,
            "height": 0.35,
            "font_size": 12,
        },
    ]

    slides = analyze_rebuild_layout(blocks)
    first_slide = slides[0]

    assert [block["text_role"] for block in first_slide] == ["title", "image", "caption"]
    assert first_slide[2]["x"] == first_slide[1]["x"]
    assert first_slide[2]["width"] <= first_slide[1]["width"]


def test_analyze_rebuild_layout_preserves_two_column_body_blocks_separately():
    blocks = [
        {"text": "Execution review", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.2, "height": 0.7, "font_size": 30},
        {"text": "Left column summary", "slide_index": 0, "x": 1, "y": 2.0, "width": 4.1, "height": 0.45, "font_size": 18},
        {"text": "Right column summary", "slide_index": 0, "x": 7.1, "y": 2.02, "width": 4.0, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    first_slide = slides[0]

    assert [block["text"] for block in first_slide] == ["Execution review", "Left column summary", "Right column summary"]
    assert [block["text_role"] for block in first_slide] == ["title", "body", "body"]
    assert first_slide[1]["x"] < first_slide[2]["x"]
    assert first_slide[1]["column_index"] == 0
    assert first_slide[2]["column_index"] == 1


def test_analyze_rebuild_layout_detects_simple_text_tables():
    blocks = [
        {"text": "Quarterly metrics", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.4, "height": 0.7, "font_size": 28},
        {"text": "Region", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 2.1, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 4.0, "y": 2.0, "width": 2.1, "height": 0.45, "font_size": 18},
        {"text": "APAC", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 2.1, "height": 0.45, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 4.0, "y": 2.7, "width": 2.1, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    first_slide = slides[0]

    assert [block["text_role"] for block in first_slide] == ["title", "table"]
    table_block = first_slide[1]
    assert table_block["rows"] == 2
    assert table_block["cols"] == 2
    assert table_block["cells"][0][0]["text"] == "Region"
    assert table_block["cells"][0][1]["text"] == "Revenue"
    assert table_block["cells"][1][0]["text"] == "APAC"
    assert table_block["cells"][1][1]["text"] == "$2.4M"


def test_analyze_rebuild_layout_detects_tables_with_small_ocr_jitter():
    blocks = [
        {"text": "Quarterly metrics", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.4, "height": 0.7, "font_size": 28},
        {"text": "Region", "slide_index": 0, "x": 1.02, "y": 2.01, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 4.08, "y": 2.03, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "APAC", "slide_index": 0, "x": 0.98, "y": 2.73, "width": 2.05, "height": 0.45, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 4.05, "y": 2.68, "width": 2.1, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["text_role"] == "table"
    assert table_block["rows"] == 2
    assert table_block["cols"] == 2


def test_analyze_rebuild_layout_preserves_relative_table_column_widths():
    blocks = [
        {"text": "Pipeline status", "slide_index": 0, "x": 1, "y": 0.8, "width": 4.2, "height": 0.7, "font_size": 28},
        {"text": "Stage", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 3.1, "height": 0.45, "font_size": 18},
        {"text": "Count", "slide_index": 0, "x": 4.7, "y": 2.0, "width": 1.2, "height": 0.45, "font_size": 18},
        {"text": "Qualified", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 3.1, "height": 0.45, "font_size": 18},
        {"text": "18", "slide_index": 0, "x": 4.7, "y": 2.7, "width": 1.2, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["column_widths"][0] > table_block["column_widths"][1]


def test_analyze_rebuild_layout_detects_header_cells_that_span_multiple_columns():
    blocks = [
        {"text": "Regional performance", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.2, "height": 0.6, "font_size": 26},
        {"text": "Q1 2026", "slide_index": 0, "x": 1.0, "y": 1.5, "width": 4.9, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 3.1, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 4.7, "y": 2.0, "width": 1.2, "height": 0.45, "font_size": 18},
        {"text": "APAC", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 3.1, "height": 0.45, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 4.7, "y": 2.7, "width": 1.2, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    first_slide = slides[0]

    assert [block["text_role"] for block in first_slide] == ["title", "table"]
    table_block = first_slide[1]
    assert table_block["rows"] == 3
    assert table_block["cols"] == 2
    assert table_block["cells"][0][0]["text"] == "Q1 2026"
    assert table_block["cells"][0][0]["colspan"] == 2
    assert table_block["cells"][0][1]["merged"] is True
    assert table_block["cells"][1][0]["text"] == "Region"
    assert table_block["cells"][1][1]["text"] == "Revenue"


def test_analyze_rebuild_layout_detects_first_column_cells_that_span_two_rows():
    blocks = [
        {"text": "Segment performance", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.2, "height": 0.6, "font_size": 26},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 1.6, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.5, "y": 1.6, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 5.7, "y": 1.6, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.3, "width": 2.0, "height": 1.0, "font_size": 18},
        {"text": "APAC", "slide_index": 0, "x": 3.5, "y": 2.3, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 5.7, "y": 2.3, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "EMEA", "slide_index": 0, "x": 3.5, "y": 2.9, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "$1.8M", "slide_index": 0, "x": 5.7, "y": 2.9, "width": 1.4, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 3
    assert table_block["cols"] == 3
    assert table_block["cells"][1][0]["text"] == "Enterprise"
    assert table_block["cells"][1][0]["rowspan"] == 2
    assert table_block["cells"][2][0]["merged"] is True
    assert table_block["cells"][1][1]["text"] == "APAC"
    assert table_block["cells"][2][1]["text"] == "EMEA"


def test_analyze_rebuild_layout_detects_first_column_cells_that_span_three_rows():
    blocks = [
        {"text": "Segment performance", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.2, "height": 0.6, "font_size": 26},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 1.6, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.5, "y": 1.6, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 5.7, "y": 1.6, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.3, "width": 2.0, "height": 1.65, "font_size": 18},
        {"text": "APAC", "slide_index": 0, "x": 3.5, "y": 2.3, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 5.7, "y": 2.3, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "EMEA", "slide_index": 0, "x": 3.5, "y": 2.9, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "$1.8M", "slide_index": 0, "x": 5.7, "y": 2.9, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Americas", "slide_index": 0, "x": 3.5, "y": 3.5, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "$3.1M", "slide_index": 0, "x": 5.7, "y": 3.5, "width": 1.4, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 4
    assert table_block["cols"] == 3
    assert table_block["cells"][1][0]["text"] == "Enterprise"
    assert table_block["cells"][1][0]["rowspan"] == 3
    assert table_block["cells"][2][0]["merged"] is True
    assert table_block["cells"][3][0]["merged"] is True
    assert table_block["cells"][3][1]["text"] == "Americas"
    assert table_block["cells"][3][2]["text"] == "$3.1M"


def test_analyze_rebuild_layout_detects_non_first_column_cells_that_span_two_rows():
    blocks = [
        {"text": "Operations review", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.2, "height": 0.6, "font_size": 26},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 1.6, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.5, "y": 1.6, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 5.7, "y": 1.6, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.3, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "APAC + EMEA", "slide_index": 0, "x": 3.5, "y": 2.3, "width": 1.7, "height": 1.0, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 5.7, "y": 2.3, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.9, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "$1.8M", "slide_index": 0, "x": 5.7, "y": 2.9, "width": 1.4, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 3
    assert table_block["cols"] == 3
    assert table_block["cells"][1][1]["text"] == "APAC + EMEA"
    assert table_block["cells"][1][1]["rowspan"] == 2
    assert table_block["cells"][2][1]["merged"] is True
    assert table_block["cells"][1][0]["text"] == "Enterprise"
    assert table_block["cells"][2][2]["text"] == "$1.8M"


def test_analyze_rebuild_layout_detects_non_first_column_cells_that_span_three_rows():
    blocks = [
        {"text": "Operations review", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.2, "height": 0.6, "font_size": 26},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 1.6, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.5, "y": 1.6, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 5.7, "y": 1.6, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.3, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "APAC + EMEA + Americas", "slide_index": 0, "x": 3.5, "y": 2.3, "width": 1.7, "height": 1.65, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 5.7, "y": 2.3, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.9, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "$1.8M", "slide_index": 0, "x": 5.7, "y": 2.9, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 3.5, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "$3.1M", "slide_index": 0, "x": 5.7, "y": 3.5, "width": 1.4, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 4
    assert table_block["cols"] == 3
    assert table_block["cells"][1][1]["text"] == "APAC + EMEA + Americas"
    assert table_block["cells"][1][1]["rowspan"] == 3
    assert table_block["cells"][2][1]["merged"] is True
    assert table_block["cells"][3][1]["merged"] is True
    assert table_block["cells"][3][2]["text"] == "$3.1M"


def test_analyze_rebuild_layout_detects_two_level_table_headers():
    blocks = [
        {"text": "Business review", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.2, "height": 0.6, "font_size": 26},
        {"text": "Commercial", "slide_index": 0, "x": 1.0, "y": 1.5, "width": 4.9, "height": 0.45, "font_size": 18},
        {"text": "Operations", "slide_index": 0, "x": 5.7, "y": 1.5, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Revenue", "slide_index": 0, "x": 3.5, "y": 2.0, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "Utilization", "slide_index": 0, "x": 5.7, "y": 2.0, "width": 1.4, "height": 0.45, "font_size": 18},
        {"text": "APAC", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "$2.4M", "slide_index": 0, "x": 3.5, "y": 2.7, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "81%", "slide_index": 0, "x": 5.7, "y": 2.7, "width": 1.4, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 3
    assert table_block["cols"] == 3
    assert table_block["header_rows"] == 2
    assert table_block["cells"][0][0]["text"] == "Commercial"
    assert table_block["cells"][0][0]["colspan"] == 2
    assert table_block["cells"][0][1]["merged"] is True
    assert table_block["cells"][1][0]["text"] == "Region"
    assert table_block["cells"][1][1]["text"] == "Revenue"
    assert table_block["cells"][1][2]["text"] == "Utilization"


def test_analyze_rebuild_layout_detects_constrained_cross_merges():
    blocks = [
        {"text": "Business review", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.4, "height": 0.6, "font_size": 26},
        {"text": "Commercial", "slide_index": 0, "x": 1.0, "y": 1.5, "width": 4.8, "height": 0.45, "font_size": 18},
        {"text": "Operations", "slide_index": 0, "x": 5.6, "y": 1.5, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.4, "y": 2.0, "width": 1.7, "height": 0.45, "font_size": 18},
        {"text": "Utilization", "slide_index": 0, "x": 5.6, "y": 2.0, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 2.0, "height": 1.0, "font_size": 18},
        {"text": "APAC + EMEA", "slide_index": 0, "x": 3.4, "y": 2.7, "width": 1.7, "height": 1.0, "font_size": 18},
        {"text": "81%", "slide_index": 0, "x": 5.6, "y": 2.7, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "79%", "slide_index": 0, "x": 5.6, "y": 3.3, "width": 1.6, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 4
    assert table_block["cols"] == 3
    assert table_block["header_rows"] == 2
    assert table_block["cells"][0][0]["text"] == "Commercial"
    assert table_block["cells"][0][0]["colspan"] == 2
    assert table_block["cells"][0][1]["merged"] is True
    assert table_block["cells"][2][0]["text"] == "Enterprise"
    assert table_block["cells"][2][0]["rowspan"] == 2
    assert table_block["cells"][3][0]["merged"] is True
    assert table_block["cells"][2][1]["text"] == "APAC + EMEA"
    assert table_block["cells"][2][1]["rowspan"] == 2
    assert table_block["cells"][3][1]["merged"] is True
    assert table_block["cells"][3][2]["text"] == "79%"


def test_analyze_rebuild_layout_detects_multiple_non_overlapping_cross_merges():
    blocks = [
        {"text": "Business review", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 6.6, "height": 0.6, "font_size": 26},
        {"text": "Commercial", "slide_index": 0, "x": 1.0, "y": 1.5, "width": 4.9, "height": 0.45, "font_size": 18},
        {"text": "Operations", "slide_index": 0, "x": 5.8, "y": 1.5, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.4, "y": 2.0, "width": 1.8, "height": 0.45, "font_size": 18},
        {"text": "Utilization", "slide_index": 0, "x": 5.8, "y": 2.0, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 2.0, "height": 1.0, "font_size": 18},
        {"text": "APAC + EMEA", "slide_index": 0, "x": 3.4, "y": 2.7, "width": 1.8, "height": 1.0, "font_size": 18},
        {"text": "81%", "slide_index": 0, "x": 5.8, "y": 2.7, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "79%", "slide_index": 0, "x": 5.8, "y": 3.3, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "Consumer", "slide_index": 0, "x": 1.0, "y": 4.0, "width": 2.0, "height": 1.0, "font_size": 18},
        {"text": "Americas + LATAM", "slide_index": 0, "x": 3.4, "y": 4.0, "width": 1.8, "height": 1.0, "font_size": 18},
        {"text": "74%", "slide_index": 0, "x": 5.8, "y": 4.0, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "71%", "slide_index": 0, "x": 5.8, "y": 4.6, "width": 1.6, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 6
    assert table_block["cols"] == 3
    assert table_block["header_rows"] == 2
    assert table_block["cells"][0][0]["colspan"] == 2
    assert table_block["cells"][2][0]["rowspan"] == 2
    assert table_block["cells"][2][1]["rowspan"] == 2
    assert table_block["cells"][4][0]["rowspan"] == 2
    assert table_block["cells"][4][1]["rowspan"] == 2
    assert table_block["cells"][3][0]["merged"] is True
    assert table_block["cells"][3][1]["merged"] is True
    assert table_block["cells"][5][0]["merged"] is True
    assert table_block["cells"][5][1]["merged"] is True
    assert table_block["cells"][5][2]["text"] == "71%"


def test_analyze_rebuild_layout_detects_freer_cross_merge_combinations_without_conflicts():
    blocks = [
        {"text": "Portfolio review", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 7.4, "height": 0.6, "font_size": 26},
        {"text": "Commercial", "slide_index": 0, "x": 1.0, "y": 1.5, "width": 4.8, "height": 0.45, "font_size": 18},
        {"text": "Operations", "slide_index": 0, "x": 5.8, "y": 1.5, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "Customer", "slide_index": 0, "x": 7.7, "y": 1.5, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.4, "y": 2.0, "width": 1.8, "height": 0.45, "font_size": 18},
        {"text": "Utilization", "slide_index": 0, "x": 5.8, "y": 2.0, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "NPS", "slide_index": 0, "x": 7.7, "y": 2.0, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 2.0, "height": 1.0, "font_size": 18},
        {"text": "APAC + EMEA", "slide_index": 0, "x": 3.4, "y": 2.7, "width": 1.8, "height": 1.0, "font_size": 18},
        {"text": "81%", "slide_index": 0, "x": 5.8, "y": 2.7, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "57", "slide_index": 0, "x": 7.7, "y": 2.7, "width": 1.5, "height": 1.0, "font_size": 18},
        {"text": "79%", "slide_index": 0, "x": 5.8, "y": 3.3, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "Consumer", "slide_index": 0, "x": 1.0, "y": 4.0, "width": 2.0, "height": 1.0, "font_size": 18},
        {"text": "Americas + LATAM", "slide_index": 0, "x": 3.4, "y": 4.0, "width": 1.8, "height": 1.0, "font_size": 18},
        {"text": "74%", "slide_index": 0, "x": 5.8, "y": 4.0, "width": 1.6, "height": 0.45, "font_size": 18},
        {"text": "49", "slide_index": 0, "x": 7.7, "y": 4.0, "width": 1.5, "height": 1.0, "font_size": 18},
        {"text": "71%", "slide_index": 0, "x": 5.8, "y": 4.6, "width": 1.6, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 6
    assert table_block["cols"] == 4
    assert table_block["header_rows"] == 2
    assert table_block["cells"][0][0]["colspan"] == 2
    assert table_block["cells"][2][0]["rowspan"] == 2
    assert table_block["cells"][2][1]["rowspan"] == 2
    assert table_block["cells"][2][3]["rowspan"] == 2
    assert table_block["cells"][4][0]["rowspan"] == 2
    assert table_block["cells"][4][1]["rowspan"] == 2
    assert table_block["cells"][4][3]["rowspan"] == 2
    assert table_block["cells"][5][2]["text"] == "71%"


def test_analyze_rebuild_layout_detects_four_column_complex_tables_from_raw_ocr_boxes():
    blocks = [
        {"text": "Strategy matrix", "slide_index": 0, "x": 1.0, "y": 0.8, "width": 7.8, "height": 0.6, "font_size": 26},
        {"text": "Commercial", "slide_index": 0, "x": 1.0, "y": 1.5, "width": 4.2, "height": 0.45, "font_size": 18},
        {"text": "Operations", "slide_index": 0, "x": 5.5, "y": 1.5, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "Customer", "slide_index": 0, "x": 7.2, "y": 1.5, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "Category", "slide_index": 0, "x": 1.0, "y": 2.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Region", "slide_index": 0, "x": 3.2, "y": 2.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "Utilization", "slide_index": 0, "x": 5.5, "y": 2.0, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "NPS", "slide_index": 0, "x": 7.2, "y": 2.0, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "Enterprise", "slide_index": 0, "x": 1.0, "y": 2.7, "width": 2.0, "height": 1.0, "font_size": 18},
        {"text": "APAC", "slide_index": 0, "x": 3.2, "y": 2.7, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "81%", "slide_index": 0, "x": 5.5, "y": 2.7, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "57", "slide_index": 0, "x": 7.2, "y": 2.7, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "EMEA", "slide_index": 0, "x": 3.2, "y": 3.3, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "79%", "slide_index": 0, "x": 5.5, "y": 3.3, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "55", "slide_index": 0, "x": 7.2, "y": 3.3, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "Consumer", "slide_index": 0, "x": 1.0, "y": 4.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "LATAM", "slide_index": 0, "x": 3.2, "y": 4.0, "width": 2.0, "height": 0.45, "font_size": 18},
        {"text": "74%", "slide_index": 0, "x": 5.5, "y": 4.0, "width": 1.5, "height": 0.45, "font_size": 18},
        {"text": "49", "slide_index": 0, "x": 7.2, "y": 4.0, "width": 1.5, "height": 0.45, "font_size": 18},
    ]

    slides = analyze_rebuild_layout(blocks)
    table_block = slides[0][1]

    assert table_block["rows"] == 5
    assert table_block["cols"] == 4
    assert table_block["header_rows"] == 2
    assert table_block["cells"][0][0]["colspan"] == 2
    assert table_block["cells"][2][0]["rowspan"] == 2
    assert table_block["cells"][3][0]["merged"] is True
    assert table_block["cells"][3][1]["text"] == "EMEA"
    assert table_block["cells"][4][3]["text"] == "49"
