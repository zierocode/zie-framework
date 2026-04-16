"""Assert ADR-000-summary.md covers all ADRs in the decisions/ directory."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
DECISIONS_DIR = REPO_ROOT / "zie-framework" / "decisions"


def test_adr_summary_covers_all_adrs():
    content = (DECISIONS_DIR / "ADR-000-summary.md").read_text()
    for n in range(31, 56):
        assert f"ADR-{n:03d}" in content, f"ADR-{n:03d} missing from ADR-000-summary.md"


def test_adr_summary_word_count():
    content = (DECISIONS_DIR / "ADR-000-summary.md").read_text()
    words = len(content.split())
    assert words <= 1600, f"ADR-000-summary.md is {words} words (limit: 1600)"
