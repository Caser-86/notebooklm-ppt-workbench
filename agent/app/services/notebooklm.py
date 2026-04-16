from typing import Any


def run_generation(payload: dict[str, Any]) -> dict[str, str]:
    if not payload.get("browser_ready"):
        return {
            "status": "needs_attention",
            "attention_reason": "browser_login_required",
        }
    return {"status": "generating", "attention_reason": ""}


class NotebookLMRunner:
    def __init__(self, browser_profile_dir: str):
        self.browser_profile_dir = browser_profile_dir

    def launch(self) -> None:
        return None

    def submit_prompt(self, prompt: str) -> None:
        return None

    def export_deck(self) -> list[str]:
        return []
