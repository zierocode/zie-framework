---
slug: audit-safety-check-regex-precompile
status: approved
approved: true
date: 2026-04-01
spec: zie-framework/specs/2026-04-01-audit-safety-check-regex-precompile-design.md
---

# Plan: Precompile Safety-Check Regex Patterns

## Overview

Refactor `hooks/safety-check.py` to compile all regex patterns once at module
level instead of inside `_regex_check()` on every invocation. Zero behaviour
change. Verified by four new unit tests plus full regression.

---

## Task List

### Task 1 — Write failing unit tests (RED)

**File:** `tests/unit/test_safety_check_precompile.py`

**Steps:**

1. Create the test file with the four tests specified in the spec.
2. Run `make test-unit` — all four tests must FAIL (the compiled constants do
   not yet exist at module level).
3. Confirm the failure message references `DANGEROUS_PATTERNS` or
   `SAFE_PATTERNS` not being `re.Pattern` instances.

**Test file content:**

```python
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

import safety_check as sc  # noqa: E402


def test_dangerous_patterns_are_compiled():
    assert all(
        isinstance(p, re.Pattern) for p in sc.DANGEROUS_PATTERNS
    ), "DANGEROUS_PATTERNS must contain compiled re.Pattern objects"


def test_safe_patterns_are_compiled():
    assert all(
        isinstance(p, re.Pattern) for p in sc.SAFE_PATTERNS
    ), "SAFE_PATTERNS must contain compiled re.Pattern objects"


def test_pattern_count_unchanged():
    assert len(sc.DANGEROUS_PATTERNS) == len(sc.DANGEROUS_PATTERN_STRINGS), (
        "DANGEROUS_PATTERNS count must match DANGEROUS_PATTERN_STRINGS"
    )
    assert len(sc.SAFE_PATTERNS) == len(sc.SAFE_PATTERN_STRINGS), (
        "SAFE_PATTERNS count must match SAFE_PATTERN_STRINGS"
    )


def test_ignorecase_flag_preserved():
    for p in sc.DANGEROUS_PATTERNS:
        assert p.flags & re.IGNORECASE, (
            f"Pattern {p.pattern!r} missing re.IGNORECASE flag"
        )
    for p in sc.SAFE_PATTERNS:
        assert p.flags & re.IGNORECASE, (
            f"Pattern {p.pattern!r} missing re.IGNORECASE flag"
        )
```

**Verification:** `make test-unit` shows 4 failures, 0 errors.

---

### Task 2 — Add compiled constants at module level (GREEN)

**File:** `hooks/safety-check.py`

**Location:** Immediately after the `SAFE_PATTERN_STRINGS` list, before the
`# ---` separator line.

**Add these two lines:**

```python
DANGEROUS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERN_STRINGS]
SAFE_PATTERNS      = [re.compile(p, re.IGNORECASE) for p in SAFE_PATTERN_STRINGS]
```

The section after the edit:

```python
SAFE_PATTERN_STRINGS = [
    r"rm\s+-rf\s+\./",
    # ... (unchanged)
    r"rm\s+-rf\s+.*venv",
]

# Compiled once at import time
DANGEROUS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERN_STRINGS]
SAFE_PATTERNS      = [re.compile(p, re.IGNORECASE) for p in SAFE_PATTERN_STRINGS]

# ---------------------------------------------------------------------------
```

**Verification:** `make test-unit` — the four new tests turn GREEN. Full suite
still passes.

---

### Task 3 — Update `_regex_check()` to use compiled constants (REFACTOR)

**File:** `hooks/safety-check.py`

**Current `_regex_check` body:**

```python
def _regex_check(command: str) -> tuple[bool, str]:
    """
    Returns (should_block, reason).
    Compiles patterns fresh on every call today — to be precompiled.
    """
    dangerous = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERN_STRINGS]
    safe = [re.compile(p, re.IGNORECASE) for p in SAFE_PATTERN_STRINGS]

    for pattern in dangerous:
        if pattern.search(command):
            for safe_pattern in safe:
                if safe_pattern.search(command):
                    return False, ""
            return True, f"Matched dangerous pattern: {pattern.pattern}"
    return False, ""
```

**Replacement:**

```python
def _regex_check(command: str) -> tuple[bool, str]:
    """Returns (should_block, reason)."""
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(command):
            for safe_pattern in SAFE_PATTERNS:
                if safe_pattern.search(command):
                    return False, ""
            return True, f"Matched dangerous pattern: {pattern.pattern}"
    return False, ""
```

Changes:
- Remove local `dangerous` and `safe` compile calls.
- Replace iteration targets with module-level `DANGEROUS_PATTERNS` / `SAFE_PATTERNS`.
- Remove stale docstring comment about "Compiles patterns fresh on every call".

**Verification:** `make test-unit` — all tests green. No `re.compile` inside
any function body remains.

---

### Task 4 — Final regression check

```bash
make test-unit
```

Expected: all pre-existing safety-check tests pass, all four new tests pass.
Verify with grep:

```bash
grep -n 're.compile' hooks/safety-check.py
```

All matches must be on the two module-level constant lines only.

---

## File Change Summary

| File | Change |
| --- | --- |
| `hooks/safety-check.py` | Add `DANGEROUS_PATTERNS` + `SAFE_PATTERNS` module-level constants; replace `_regex_check` local compile calls with constants |
| `tests/unit/test_safety_check_precompile.py` | New file — 4 unit tests |

---

## Test Strategy

| Layer | File | What is tested |
| --- | --- | --- |
| Unit | `tests/unit/test_safety_check_precompile.py` | Compiled type, count parity, IGNORECASE flag |
| Unit (regression) | existing `tests/unit/test_safety_check*.py` | End-to-end regex blocking and allow logic |

All tests run via `make test-unit`. No integration or e2e tests required.

---

## Rollout

1. This change is in `hooks/safety-check.py` which is loaded as a subprocess each time.
   No restart required.
2. Non-breaking: `DANGEROUS_PATTERN_STRINGS` and `SAFE_PATTERN_STRINGS` remain in the
   module for backward compatibility and for the count-parity test.
3. No config changes. No migration steps.
