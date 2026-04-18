from app.services.pptx_import import classify_pptx_source, extract_pptx_assets


def test_classify_internal_generated_pptx(build_fixture_pptx, tmp_path):
    pptx_path = build_fixture_pptx("internal-generated.pptx", ["Editable rebuild"])

    result = classify_pptx_source(pptx_path)

    assert result == "internal_generated"


def test_extract_import_assets_creates_slide_entries(build_fixture_pptx, tmp_path):
    pptx_path = build_fixture_pptx("notebooklm-export.pptx", ["NotebookLM export"])

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert bundle.source_type == "notebooklm_export"
    assert bundle.page_count == 1
    assert bundle.slides[0].slide_index == 1
    assert bundle.slides[0].preview_image_path.endswith("slide-1.png")
    assert "NotebookLM export" in bundle.slides[0].text_dump


def test_extract_pptx_text_boxes_as_imported_text_blocks(build_fixture_pptx, tmp_path):
    pptx_path = build_fixture_pptx("text-blocks.pptx", ["Quarterly update"])

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert bundle.slides[0].blocks[0]["content_type"] == "imported_text"
    assert bundle.slides[0].blocks[0]["text_role"] == "title"
    assert bundle.slides[0].blocks[0]["text"] == "Quarterly update"


def test_extract_pptx_picture_as_imported_image_block(build_fixture_pptx_with_picture, tmp_path):
    pptx_path = build_fixture_pptx_with_picture("picture-blocks.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert any(block["content_type"] == "imported_image" for block in bundle.slides[0].blocks)


def test_extract_powerpoint_table_as_imported_table_block(build_fixture_pptx_with_table, tmp_path):
    pptx_path = build_fixture_pptx_with_table("table-blocks.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    table_block = next(block for block in bundle.slides[0].blocks if block["content_type"] == "imported_table")
    assert table_block["rows"] == 2
    assert table_block["cols"] == 2
    assert table_block["cells"][0][0]["text"] == "Metric"


def test_group_imported_icon_card_objects(build_fixture_pptx_with_icon_card, tmp_path):
    pptx_path = build_fixture_pptx_with_icon_card("icon-card-blocks.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert any(block["content_type"] == "imported_icon_card" for block in bundle.slides[0].blocks)


def test_extract_powerpoint_chart_as_imported_chart_block(build_fixture_pptx_with_chart, tmp_path):
    pptx_path = build_fixture_pptx_with_chart("chart-blocks.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    chart_block = next(block for block in bundle.slides[0].blocks if block["content_type"] == "imported_chart")
    assert chart_block["chart_type"]
    assert chart_block["series"]


def test_extract_group_shape_emits_unsupported_group(build_fixture_pptx_with_group_shape, tmp_path):
    pptx_path = build_fixture_pptx_with_group_shape("group-blocks.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    assert any(block["content_type"] == "unsupported_group" for block in bundle.slides[0].blocks)


def test_group_shape_promotes_supported_text_children(build_fixture_pptx_with_group_shape, tmp_path):
    pptx_path = build_fixture_pptx_with_group_shape("group-promote.pptx")

    bundle = extract_pptx_assets(project_id=1, pptx_path=pptx_path, import_dir=tmp_path)

    promoted_texts = [block for block in bundle.slides[0].blocks if block["content_type"] == "imported_text"]

    assert any(block["text"] == "Grouped title" for block in promoted_texts)
    assert any(block["text"] == "Grouped body" for block in promoted_texts)
