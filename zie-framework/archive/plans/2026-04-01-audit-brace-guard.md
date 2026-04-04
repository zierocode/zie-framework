---
slug: audit-brace-guard
status: approved
approved: true
date: 2026-04-01
---

# Plan: Block Bare Braces in Confirmation Wrapper Safety Check

## Overview

Add `{` and `}` to `_DANGEROUS_COMPOUND_RE` in `hooks/input-sanitizer.py`.
A bare `}` in the command string structurally breaks the `{{ {command}; }}`
shell wrapper. Single-character addition to the existing regex.

**Spec:** `zie-framework/specs/2026-04-01-audit-brace-guard-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `}` in command → `_is_safe_for_confirmation_wrapper` returns False |
| AC-2 | `{` in command → `_is_safe_for_confirmation_wrapper` returns False |
| AC-3 | Single `|` (pipe) still returns True (existing behavior preserved) |
| AC-4 | Plain command (`ls -la`) still returns True |
| AC-5 | All tests pass; `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Write failing tests (RED)

**File:** `tests/unit/test_input_sanitizer.py`

Add `TestBraceGuard` class (or add to existing `_is_safe_for_confirmation_wrapper` test class):

```python
from hooks.input_sanitizer import _is_safe_for_confirmation_wrapper


class TestBraceGuard:
    def test_brace_close_blocked(self):
        """AC-1."""
        assert _is_safe_for_confirmation_wrapper("echo }") is False

    def test_brace_open_blocked(self):
        """AC-2."""
        assert _is_safe_for_confirmation_wrapper("echo {foo") is False

    def test_pipe_still_allowed(self):
        """AC-3."""
        assert _is_safe_for_confirmation_wrapper("cat file | grep foo") is True

    def test_plain_command_allowed(self):
        """AC-4."""
        assert _is_safe_for_confirmation_wrapper("ls -la") is True
```

Run `make test-unit` — RED confirmed (AC-1 and AC-2 fail).

---

### Task 2 — Implement (GREEN)

**File:** `hooks/input-sanitizer.py`

**Before (line 34):**
```python
_DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\()')
```

**After:**
```python
_DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}])')
```

Run `make test-unit` — GREEN.

---

### Task 3 — Full suite gate

Run `make test-ci` — must exit 0.

---

## Test Strategy

| Layer | Test | AC |
|-------|------|----|
| Unit | test_brace_close_blocked | AC-1 |
| Unit | test_brace_open_blocked | AC-2 |
| Unit | test_pipe_still_allowed | AC-3 |
| Unit | test_plain_command_allowed | AC-4 |

---

## Rollout

1. Write failing tests (Task 1) — RED.
2. Apply single str_replace to input-sanitizer.py (Task 2) — GREEN.
3. Run `make test-ci` (Task 3) — no regression.
4. Mark ROADMAP Done.
