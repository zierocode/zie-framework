"""Verify ADR-026 exists for the roadmap-done-compaction decision."""
import sys
from pathlib import Path

DECISIONS_DIR = Path(__file__).parents[2] / "zie-framework" / "decisions"


def test_adr_026_file_exists():
    matches = list(DECISIONS_DIR.glob("ADR-026-*.md"))
    assert matches, "ADR-026-roadmap-done-compaction.md must exist in zie-framework/decisions/"


def test_adr_026_has_required_sections():
    matches = list(DECISIONS_DIR.glob("ADR-026-*.md"))
    assert matches, "ADR-026 not found"
    content = matches[0].read_text(encoding="utf-8")
    assert "## Context" in content
    assert "## Decision" in content
    assert "## Consequences" in content


def test_compact_roadmap_done_importable():
    sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
    from utils import compact_roadmap_done
    assert callable(compact_roadmap_done)
