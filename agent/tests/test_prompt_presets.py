from app.services.prompts import build_generation_prompt, get_prompt_presets


def test_get_prompt_presets_returns_three_named_presets():
    presets = get_prompt_presets()
    assert [preset["id"] for preset in presets] == ["default", "investor", "teaching"]


def test_build_generation_prompt_includes_source_summary():
    prompt = build_generation_prompt(
        preset_id="default",
        user_prompt="Make it concise",
        source_summary="Market share grew 22 percent",
    )
    assert "Make it concise" in prompt
    assert "Market share grew 22 percent" in prompt
