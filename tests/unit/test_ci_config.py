"""Tests for CI configuration and CLAUDE.md integration test documentation."""
import re
from pathlib import Path

CI_YML = Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"
CLAUDE_MD = Path(__file__).parents[2] / "CLAUDE.md"


def test_ci_runs_make_test_unit():
    """CI must run make test-unit, not make test (integration tests need live Claude)."""
    text = CI_YML.read_text()
    assert "make test-unit" in text, "ci.yml must run 'make test-unit'"
    assert re.search(r'^\s*run:\s*make test\s*$', text, re.MULTILINE) is None, (
        "ci.yml must not run bare 'make test' (includes integration tests)"
    )


def test_ci_preserves_branch_filter():
    """CI branch filter must include both main and dev."""
    text = CI_YML.read_text()
    assert "main" in text
    assert "dev" in text


def test_claude_md_documents_integration_test_exclusion():
    """CLAUDE.md must note that integration tests require live Claude session."""
    text = CLAUDE_MD.read_text()
    assert "make test-int" in text
    assert "live" in text.lower() or "session" in text.lower(), (
        "CLAUDE.md must explain why make test-int is excluded from CI"
    )
