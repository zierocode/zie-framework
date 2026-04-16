"""Tests for CLAUDE.md — verifies make test-fast and make test-ci are documented."""

from pathlib import Path

CLAUDE_MD = Path(__file__).parents[2] / "CLAUDE.md"


def _text():
    return CLAUDE_MD.read_text()


def test_test_fast_documented():
    assert "make test-fast" in _text(), "CLAUDE.md must document make test-fast"


def test_test_ci_documented():
    assert "make test-ci" in _text(), "CLAUDE.md must document make test-ci"


def test_test_fast_has_description():
    text = _text()
    idx = text.index("make test-fast")
    snippet = text[idx : idx + 120]
    assert "TDD" in snippet or "fast" in snippet.lower() or "RED" in snippet, (
        "make test-fast entry should describe TDD / fast feedback use"
    )


def test_test_ci_has_description():
    text = _text()
    idx = text.index("make test-ci")
    snippet = text[idx : idx + 120]
    assert "commit" in snippet.lower() or "full" in snippet.lower() or "CI" in snippet, (
        "make test-ci entry should describe pre-commit / full suite use"
    )


def test_test_unit_still_present():
    assert "make test-unit" in _text(), "make test-unit must remain documented"
