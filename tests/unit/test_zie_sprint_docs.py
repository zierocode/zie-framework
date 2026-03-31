"""Tests that /zie-sprint is documented in CLAUDE.md and zie-status."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _claude_md():
    return (REPO_ROOT / "CLAUDE.md").read_text()


def _status_cmd():
    return (REPO_ROOT / "commands" / "zie-status.md").read_text()


class TestClaudeMdDocumentation:
    def test_zie_sprint_in_claude_md(self):
        assert "/zie-sprint" in _claude_md(), \
            "CLAUDE.md must mention /zie-sprint"

    def test_zie_sprint_has_description_in_claude_md(self):
        text = _claude_md()
        idx = text.index("/zie-sprint")
        snippet = text[idx:idx + 120]
        assert "sprint" in snippet.lower() or "batch" in snippet.lower() or "backlog" in snippet.lower(), \
            "/zie-sprint entry in CLAUDE.md must describe sprint clear behavior"


class TestZieStatusSuggestions:
    def test_zie_sprint_in_status_suggestions(self):
        assert "/zie-sprint" in _status_cmd(), \
            "zie-status.md must include /zie-sprint in always-available suggestions"
