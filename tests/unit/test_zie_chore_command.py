"""Structural tests for commands/zie-chore.md."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "zie-chore.md"


def test_file_exists():
    assert CMD.exists(), "commands/zie-chore.md must exist"


def test_frontmatter_keys():
    text = CMD.read_text()
    assert "description:" in text
    assert "allowed-tools:" in text


def test_no_spec_required():
    text = CMD.read_text()
    assert "no spec" in text.lower() or "spec required" not in text.lower()


def test_done_entry_mentioned():
    text = CMD.read_text()
    assert "Done" in text or "done" in text.lower()
