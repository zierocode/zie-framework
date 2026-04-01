---
slug: audit-adr-summary-tests
status: draft
date: 2026-04-01
---
# Spec: Targeted Unit Tests for adr_summary.py Edge Cases

## Problem

`hooks/adr_summary.py` contains non-trivial extraction logic with zero test
coverage for its most failure-prone boundary cases:

- **`_first_sentence`** — called on every ADR to extract the first sentence of
  the Decision section. Three untested paths:
  - No period in text → falls back to returning the whole string stripped
  - Period at end of single-sentence text → `idx == len(text) - 1`, no `". "` match, whole string returned
  - Multi-sentence text → only the first sentence should be returned, sliced at `". "`
- **Pipe escaping in `generate_summary_table`** — line 78 does
  `decision.replace("|", "\\|")` (and line 77 for `title`). If this regresses,
  the generated Markdown table silently breaks — cells split on the literal `|`
  and corrupt every column to the right. There is currently no test that puts a
  `|` in a decision string and asserts the escaping in the output.
- **Truncation at `MAX_DECISION_LEN` (120 chars)** — `test_extract_truncates_at_120`
  tests the path via `extract_adr_row`, but `_truncate` itself is not called
  directly with a string that is exactly 120 or 121 chars, nor with a string
  containing a `|` after the truncation boundary. This leaves an interaction
  path untested.

The existing suite (`test_adr_summarization.py`) covers happy paths and the
`extract_adr_row` integration well, but imports only `extract_adr_row` and
`generate_summary_table` — the private helpers `_first_sentence` and
`_extract_decision` are not tested directly.

## Proposed Solution

Add ~6 targeted, parametrized tests to
`tests/unit/test_adr_summarization.py`. No production code changes.

Import `_first_sentence` and `_extract_decision` directly from
`hooks.adr_summary` for white-box testing of the private helpers.

### Tests to add

| # | Test name | What it covers |
|---|-----------|----------------|
| 1 | `test_first_sentence_no_period` | Input with no `.` → whole string returned |
| 2 | `test_first_sentence_period_at_end` | Single sentence ending in `.` with no trailing space → whole string returned |
| 3 | `test_first_sentence_multi_sentence` | `"Foo bar. Baz qux."` → `"Foo bar."` |
| 4 | `test_generate_summary_table_pipe_in_decision` | Decision text containing `\|` → output row contains `\\\|` (escaped) and no unescaped `\|` outside delimiters |
| 5 | `test_generate_summary_table_pipe_in_title` | Title text containing `\|` → same escaping guarantee |
| 6 | `test_first_sentence_parametrized` | Parametrize tests 1–3 as a single `@pytest.mark.parametrize` block for clean output |

Tests 1–3 and 6 can be collapsed into a single parametrized test. Tests 4–5
target the highest-risk regression path and must each assert:
- The row appears in the table
- The literal unescaped `|` from the input does NOT appear inside a cell value
  (use a regex or string split on `\n` + check cell fields)

### Import pattern

```python
from hooks.adr_summary import (
    extract_adr_row,
    generate_summary_table,
    _first_sentence,
    _extract_decision,
)
```

Python allows importing name-mangled private functions from external modules
(single-underscore convention only — no name mangling applied).

## Acceptance Criteria

- [ ] `_first_sentence` is imported and tested directly (not only via `extract_adr_row`)
- [ ] A parametrized test covers: no period, period at end of string, multi-sentence input
- [ ] A test asserts that `generate_summary_table` escapes `|` in decision text
- [ ] A test asserts that `generate_summary_table` escapes `|` in title text
- [ ] All new tests are in `tests/unit/test_adr_summarization.py` — no new files
- [ ] No production code in `hooks/adr_summary.py` is modified
- [ ] `make test-fast` passes with the new tests included
- [ ] Total new test count: ≥ 5 (parametrized cases count individually)

## Out of Scope

- Changes to `hooks/adr_summary.py` production code
- Testing `_truncate` in isolation (already covered indirectly via `test_extract_truncates_at_120`)
- Testing file I/O or Path reading (covered by `test_generate_summary_table_returns_markdown`)
- Adding tests for `extract_adr_row` number/title parsing (well-covered by existing suite)
