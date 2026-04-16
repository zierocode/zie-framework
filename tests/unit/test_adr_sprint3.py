"""Tests for ADR-023 existence and structure."""

from pathlib import Path

DECISIONS_DIR = Path(__file__).parents[2] / "zie-framework" / "decisions"


def _valid_adr(path: Path) -> list:
    """Return list of issues found in ADR file."""
    issues = []
    if not path.exists():
        return [f"{path.name} does not exist"]
    text = path.read_text()
    for section in ("Context", "Decision", "Consequences"):
        if f"## {section}" not in text:
            issues.append(f"Missing section: ## {section}")
    if "Status:" not in text:
        issues.append("Missing Status field")
    return issues


def test_adr_023_exists_and_valid():
    path = DECISIONS_DIR / "ADR-023-archive-strategy.md"
    issues = _valid_adr(path)
    assert not issues, f"ADR-023 issues: {issues}"