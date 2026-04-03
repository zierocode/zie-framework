---
slug: audit-adr-summary-tests
status: approved
approved: true
date: 2026-04-01
---

# Plan: Add Boundary Tests for adr_summary.py

## Overview

Add 7 targeted unit tests to `tests/unit/test_adr_summarization.py` covering
edge cases in `_first_sentence`, `generate_summary_table` (pipe escaping,
truncation). No source changes — tests only.

**Spec:** `zie-framework/specs/2026-04-01-audit-adr-summary-tests-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `_first_sentence("")` → `""` |
| AC-2 | `_first_sentence("No period here")` → `"No period here"` |
| AC-3 | `_first_sentence("One. Two.")` → `"One."` |
| AC-4 | `_first_sentence("End.")` → `"End."` |
| AC-5 | Decision with `|` → escaped to `\|` in table row |
| AC-6 | Decision > 80 chars → truncated at 80 with `…` |
| AC-7 | All 7 tests pass; `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Add tests (direct GREEN — tests pass against existing source)

**File:** `tests/unit/test_adr_summarization.py`

Append the following classes:

```python
from hooks.adr_summary import _first_sentence, generate_summary_table, MAX_DECISION_LEN


class TestFirstSentence:
    def test_empty_string(self):
        """AC-1."""
        assert _first_sentence("") == ""

    def test_no_period(self):
        """AC-2: no period → full string returned."""
        assert _first_sentence("No period here") == "No period here"

    def test_multi_sentence(self):
        """AC-3: only first sentence returned."""
        assert _first_sentence("One. Two.") == "One."

    def test_period_at_end(self):
        """AC-4: period at end with no following space → full string returned
        (find('. ') with space after period finds nothing)."""
        result = _first_sentence("End.")
        assert result == "End."


class TestGenerateSummaryTableEdgeCases:
    def test_pipe_in_decision_is_escaped(self, tmp_path):
        """AC-5: | in decision → \\| in output."""
        adr = tmp_path / "ADR-099-test.md"
        adr.write_text(
            "# ADR-099: Test\n\n**Status:** Accepted\n\n"
            "## Decision\n\nUse A | B for routing.\n"
        )
        table = generate_summary_table([adr])
        assert "\\|" in table
        assert "Use A | B" not in table.split("Decision |")[1]  # raw pipe not in decision cell

    def test_long_decision_truncated(self, tmp_path):
        """AC-6: decision > MAX_DECISION_LEN chars → truncated with …"""
        long_text = "X" * (MAX_DECISION_LEN + 10)
        adr = tmp_path / "ADR-098-long.md"
        adr.write_text(
            f"# ADR-098: Long\n\n**Status:** Accepted\n\n## Decision\n\n{long_text}\n"
        )
        table = generate_summary_table([adr])
        assert "…" in table
        # Ensure the cell is not longer than MAX_DECISION_LEN + 1 (the ellipsis char)
        rows = [r for r in table.splitlines() if "ADR-098" in r or "098" in r]
        assert rows, "Expected a row for ADR-098"
        decision_cell = rows[0].split("|")[3].strip()
        assert len(decision_cell) <= MAX_DECISION_LEN + 1
```

Run `make test-unit` — all 7 tests should pass immediately (source already
implements the behavior correctly; these are regression guards).

---

### Task 2 — Full suite gate

Run `make test-ci` — must exit 0.

---

## Test Strategy

| Layer | Test | AC |
|-------|------|----|
| Unit | test_empty_string | AC-1 |
| Unit | test_no_period | AC-2 |
| Unit | test_multi_sentence | AC-3 |
| Unit | test_period_at_end | AC-4 |
| Unit | test_pipe_in_decision_is_escaped | AC-5 |
| Unit | test_long_decision_truncated | AC-6 |

---

## Rollout

1. Append test classes to `test_adr_summarization.py` (Task 1).
2. Run `make test-unit` — expect 7 GREEN immediately (no source changes).
3. Run `make test-ci` (Task 2) — confirm no regression.
4. Mark ROADMAP Done.
