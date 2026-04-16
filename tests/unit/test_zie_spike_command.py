"""Structural tests for commands/spike.md."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "spike.md"


def test_file_exists():
    assert CMD.exists(), "commands/spike.md must exist"


def test_frontmatter_keys():
    text = CMD.read_text()
    assert "description:" in text
    assert "allowed-tools:" in text


def test_no_roadmap_write():
    text = CMD.read_text()
    assert "no ROADMAP" in text.lower() or "not write" in text.lower() or "does not write" in text.lower()


def test_spike_directory_mentioned():
    text = CMD.read_text()
    assert "spike-" in text
