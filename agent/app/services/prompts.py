PRESETS = {
    "default": "Create a clear deck with a strong narrative.",
    "investor": "Create an investor-focused deck with traction, risk, and roadmap.",
    "teaching": "Create a teaching deck with progressive explanation and recap.",
}


def get_prompt_presets() -> list[dict[str, str]]:
    return [{"id": key, "label": key.title(), "body": value} for key, value in PRESETS.items()]


def build_generation_prompt(preset_id: str, user_prompt: str, source_summary: str) -> str:
    preset = PRESETS[preset_id]
    return f"{preset}\n\nUser instruction:\n{user_prompt}\n\nSource summary:\n{source_summary}"
