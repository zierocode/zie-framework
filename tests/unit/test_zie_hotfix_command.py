"""Structural tests for commands/hotfix.md."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "hotfix.md"


def test_file_exists():
    assert CMD.exists(), "commands/hotfix.md must exist"


def test_frontmatter_keys():
    text = CMD.read_text()
    assert "description:" in text
    assert "argument-hint:" in text
    assert "allowed-tools:" in text
    assert "model:" in text
    assert "effort:" in text


def test_has_drift_log_write_step():
    text = CMD.read_text()
    assert ".drift-log" in text or "drift" in text.lower()


def test_has_ship_step():
    text = CMD.read_text()
    assert "/release" in text or "ship" in text.lower()


def test_slug_derivation_described():
    text = CMD.read_text()
    assert "slug" in text.lower()
