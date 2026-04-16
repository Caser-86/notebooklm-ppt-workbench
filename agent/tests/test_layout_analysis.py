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
