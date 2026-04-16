"""Unit tests for ADR summary extraction logic in hooks/adr_summary.py."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from hooks.adr_summary import extract_adr_row, generate_summary_table

NORMAL_ADR = """\
# ADR-010: Safe Write via Tmp Symlink

Some intro.

## Context

Background text.

## Decision

We will always write files via a temporary path and rename atomically to prevent partial writes. This guarantees consistency.
"""

ADR_NO_DECISION = """\
# ADR-011: OsError Defense in Depth

## Context

Some context without a Decision section.
"""

ADR_NO_DECISION_NO_PARA = """\
# ADR-012: Something

## Context

## Status
"""

ADR_LONG_DECISION = """\
# ADR-013: Long Decision Example

## Decision

We decided to adopt a very detailed approach that covers many different scenarios and edge cases including fallback handling for missing files as well as error propagation strategies across the entire system stack.
"""

ADR_MISSING_NUMBER = """\
# Safe Write

## Decision

Use tmp path.
"""


def test_extract_normal():
    number, title, decision = extract_adr_row("ADR-010-safe-write.md", NORMAL_ADR)
    assert number == "ADR-010"
    assert title == "Safe Write via Tmp Symlink"
    assert "atomic" in decision or "temporary path" in decision


def test_extract_missing_decision_uses_first_paragraph():
    number, title, decision = extract_adr_row("ADR-011-oserror.md", ADR_NO_DECISION)
    assert decision == "Some context without a Decision section."


def test_extract_missing_decision_and_paragraph_uses_placeholder():
    number, title, decision = extract_adr_row("ADR-012-something.md", ADR_NO_DECISION_NO_PARA)
    assert decision == "(no decision text)"


def test_extract_truncates_at_120():
    number, title, decision = extract_adr_row("ADR-013-long.md", ADR_LONG_DECISION)
    assert len(decision) <= 121
    assert decision.endswith("…")


def test_extract_number_from_filename():
    number, title, decision = extract_adr_row("ADR-010-safe-write.md", NORMAL_ADR)
    assert number == "ADR-010"


def test_extract_missing_number_fallback():
    number, title, decision = extract_adr_row("safe-write.md", ADR_MISSING_NUMBER)
    assert number == "???"


def test_generate_summary_table_returns_markdown(tmp_path):
    adr_files = [
        ("ADR-001-first.md", "# ADR-001: First\n\n## Decision\n\nUse X.\n"),
        ("ADR-002-second.md", "# ADR-002: Second\n\n## Decision\n\nUse Y.\n"),
    ]
    paths = []
    for name, content in adr_files:
        p = tmp_path / name
        p.write_text(content)
        paths.append(p)
    result = generate_summary_table(paths)
    assert "| ADR | Title | Decision |" in result
    assert "ADR-001" in result
    assert "ADR-002" in result


def test_generate_summary_table_empty_list():
    result = generate_summary_table([])
    assert "| ADR | Title | Decision |" in result


def test_generate_summary_table_idempotent(tmp_path):
    p = tmp_path / "ADR-001-first.md"
    p.write_text("# ADR-001: First\n\n## Decision\n\nUse X.\n")
    result1 = generate_summary_table([p])
    result2 = generate_summary_table([p])
    assert result1 == result2


# Edge case tests for _first_sentence, _truncate, and pipe-escaping
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
from adr_summary import MAX_DECISION_LEN, _first_sentence, _truncate, generate_summary_table  # noqa: F811


class TestFirstSentence:
    def test_no_period_returns_full_text(self):
        assert _first_sentence("Use X for Y") == "Use X for Y"

    def test_period_at_end_returns_full_text(self):
        assert _first_sentence("Use X.") == "Use X."

    def test_multi_sentence_returns_first_only(self):
        result = _first_sentence("Use X. Then do Y. Finally Z.")
        assert result == "Use X."

    def test_strips_leading_trailing_whitespace(self):
        assert _first_sentence("  Use X.  Rest.  ") == "Use X."


class TestTruncate:
    def test_short_string_unchanged(self):
        s = "Short text."
        assert _truncate(s) == s

    def test_exact_boundary_unchanged(self):
        s = "x" * MAX_DECISION_LEN
        assert _truncate(s) == s

    def test_over_boundary_truncated_with_ellipsis(self):
        s = "x" * (MAX_DECISION_LEN + 1)
        result = _truncate(s)
        assert result.endswith("…")
        assert len(result) == MAX_DECISION_LEN + 1  # MAX + ellipsis char


class TestPipeEscaping:
    def test_pipe_in_decision_is_escaped(self, tmp_path):
        p = tmp_path / "ADR-001-pipe.md"
        p.write_text("# ADR-001: Title\n\n## Decision\n\nUse A | B.\n")
        result = generate_summary_table([p])
        assert r"\|" in result
        assert "Use A" in result

    def test_pipe_in_title_is_escaped(self, tmp_path):
        p = tmp_path / "ADR-001-pipe.md"
        p.write_text("# ADR-001: Option A | Option B\n\n## Decision\n\nUse A.\n")
        result = generate_summary_table([p])
        # Title pipe should be escaped
        assert r"\|" in result
