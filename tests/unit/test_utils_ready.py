"""Tests for parse_roadmap_ready() in utils.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
from utils import parse_roadmap_ready  # noqa: E402

ROADMAP_WITH_READY = """
## Now
- [ ] active task

## Ready
- approved-plan-slug

## Next
- future item
"""

ROADMAP_WITHOUT_READY = """
## Now
- [ ] active task

## Next
- future item
"""

ROADMAP_EMPTY_READY = """
## Ready

## Next
- future item
"""


def test_parse_roadmap_ready_returns_items(tmp_path):
    """Returns list of items from ## Ready section."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_WITH_READY)
    result = parse_roadmap_ready(f)
    assert "approved-plan-slug" in result


def test_parse_roadmap_ready_missing_section(tmp_path):
    """Returns [] when ## Ready section absent."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_WITHOUT_READY)
    assert parse_roadmap_ready(f) == []


def test_parse_roadmap_ready_empty_section(tmp_path):
    """Returns [] when ## Ready section is present but empty."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_EMPTY_READY)
    assert parse_roadmap_ready(f) == []


def test_parse_roadmap_ready_missing_file(tmp_path):
    """Returns [] when file does not exist."""
    assert parse_roadmap_ready(tmp_path / "nonexistent.md") == []


def test_parse_roadmap_ready_warn_on_empty(tmp_path, capsys):
    """warn_on_empty=True prints warning to stderr when section empty."""
    f = tmp_path / "ROADMAP.md"
    f.write_text(ROADMAP_EMPTY_READY)
    parse_roadmap_ready(f, warn_on_empty=True)
    captured = capsys.readouterr()
    assert "[zie-framework]" in captured.err
    assert "Ready" in captured.err
