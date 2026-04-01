---
slug: audit-weak-keyword-assertions
status: approved
approved: true
date: 2026-04-01
---

# Plan: Replace Keyword-in-Content Assertions with Structural Checks

## Overview

Incrementally replace `assert "keyword" in read("commands/...")` patterns with
structural checks in `test_sdlc_gates.py` and `test_sdlc_pipeline.py`.
Prioritize the `zie-implement` and `zie-release` command files as the
highest-traffic commands. Target: replace 10 keyword assertions with section
header + frontmatter presence checks.

**Spec:** `zie-framework/specs/2026-04-01-audit-weak-keyword-assertions-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | At least 10 `assert "keyword" in read(...)` assertions replaced in the two target files |
| AC-2 | Replacement assertions check structural properties (section headers `## Phase`, frontmatter keys, ordered phase appearance) |
| AC-3 | All existing tests still pass; `make test-ci` exits 0 |
| AC-4 | No tests are deleted — only converted |

---

## Tasks

### Task 1 — Audit existing assertions (pre-condition)

```bash
grep -n 'assert.*in read.*commands/zie-implement\|assert.*in read.*commands/zie-release' \
    tests/unit/test_sdlc_gates.py tests/unit/test_sdlc_pipeline.py | head -20
```

Record the 10 weakest (single-word keyword checks) as conversion targets.

---

### Task 2 — Write structural helper and replacements

**File:** `tests/unit/test_sdlc_gates.py` (and `test_sdlc_pipeline.py` as needed)

Add a helper at the top of the test file (or conftest.py if shared):

```python
def assert_sections_ordered(content: str, *headers: str) -> None:
    """Assert that headers appear in content in the given order."""
    positions = []
    for h in headers:
        idx = content.find(h)
        assert idx != -1, f"Section header not found: {h!r}"
        positions.append(idx)
    assert positions == sorted(positions), \
        f"Sections out of order: {list(zip(headers, positions))}"
```

**Example replacements for zie-implement:**

Before:
```python
assert "RED" in content
assert "GREEN" in content
assert "REFACTOR" in content
```

After:
```python
assert_sections_ordered(content, "## Phase", "RED", "GREEN", "REFACTOR")
```

Before:
```python
assert "Task" in content
```

After:
```python
# Assert task structure exists (at least one task section)
assert content.count("### Task") >= 1 or content.count("## Task") >= 1
```

**Example replacements for zie-release:**

Before:
```python
assert "merge" in content
assert "version" in content
```

After:
```python
assert "## " in content  # at least one section header
lines = content.splitlines()
header_lines = [l for l in lines if l.startswith("## ") or l.startswith("### ")]
assert len(header_lines) >= 3, f"Expected ≥3 section headers, got: {header_lines}"
```

Apply to 10 assertions total across the two files.

---

### Task 3 — Full suite gate

Run `make test-ci` — must exit 0.

---

## Test Strategy

This plan converts existing tests — it does not add new coverage. The goal is
to make the assertions meaningful rather than add new test count.

---

## Rollout

1. Run audit grep (Task 1) — identify 10 targets.
2. Add helper + apply replacements (Task 2).
3. Run `make test-unit` after each file to confirm GREEN after each change.
4. Run `make test-ci` (Task 3) — full suite gate.
5. Mark ROADMAP Done.
