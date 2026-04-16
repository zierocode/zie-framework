"""Structural tests: /spike must add spike-*/ to .gitignore."""

from pathlib import Path

SPIKE_CMD = Path(__file__).parents[2] / "commands" / "spike.md"


def test_spike_adds_gitignore_entry():
    """spike.md must instruct adding spike-*/ to .gitignore."""
    text = SPIKE_CMD.read_text()
    assert "gitignore" in text.lower() and "spike-*/" in text, (
        "commands/spike.md must add 'spike-*/' to .gitignore when creating sandbox"
    )


def test_spike_throwaway_note():
    """spike.md must note that spike directories are throwaway."""
    text = SPIKE_CMD.read_text()
    assert "throwaway" in text.lower() or "discard" in text.lower(), (
        "commands/spike.md must note that spike directories are throwaway artifacts"
    )
