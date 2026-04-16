from app.services.notebooklm import run_generation


def test_run_generation_returns_generating_when_auto_path_available():
    result = run_generation({"mode": "auto", "browser_ready": True, "prompt": "Deck prompt"})
    assert result["status"] == "generating"


def test_run_generation_returns_needs_attention_when_browser_not_ready():
    result = run_generation({"mode": "auto", "browser_ready": False, "prompt": "Deck prompt"})
    assert result["status"] == "needs_attention"
    assert result["attention_reason"] == "browser_login_required"
