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
