---
approved: true
approved_at: 2026-04-02
backlog: backlog/qwen3-coder-next-deep-review.md
spec: specs/2026-04-02-qwen3-coder-next-deep-review-design.md
---

# Plan: Qwen3-coder-next Deep Review — Hook & Compatibility Fixes

**Status:** APPROVED  
**Date:** 2026-04-02  
**approved:** true

---

## Summary

Fix 10 compatibility issues when zie-framework is used with `qwen3-coder-next:cloud` model:
- 3 CRITICAL: hooks.json syntax, claude CLI dependency, symlink handling
- 3 HIGH: knowledge-hash logic, intent-sdlc case-insensitive, metachar guard
- 4 LOW: timeout calc, glob filtering, decision fallback

---

## Dependencies

None — standalone fixes.

---

## Tasks

### Task 1: Fix `async: true` → `background: true` in hooks.json

**File:** `hooks/hooks.json`

**AC1:** Replace `"async": true` with `"background": true` in:
- `session-learn.py` hook invocation (line 130-131)
- `session-cleanup.py` hook invocation (line 135-136)
- `subagent-stop.py` hook invocation (line 156-158)

**Risk:** LOW — config only change.

---

### Task 2: Add CLI check in safety_check_agent.py

**File:** `hooks/safety_check_agent.py`

**AC2:** Before calling `claude` CLI:
1. Check if `claude` CLI exists using `shutil.which("claude")`
2. If not found, fall back to regex-only mode
3. Log warning to stderr

**Risk:** LOW — graceful degradation pattern.

---

### Task 3: Fix symlink handling in session-resume.py

**File:** `hooks/session-resume.py`

**AC3:** Lines 109-116: After warning for symlink, add `sys.exit(0)` instead of continuing.

**Risk:** LOW — defensive coding.

---

### Task 4: Fix EXCLUDE_PATHS logic in knowledge-hash.py

**File:** `hooks/knowledge-hash.py`

**AC4:** Line 44: Change from `any(ex in p.parts for ex in EXCLUDE)` to `str(p.relative_to(root))` comparison.

**Risk:** MEDIUM — could change hash computation.

**Test:** Run `python3 hooks/knowledge-hash.py --check` before/after.

---

### Task 5: Add IGNORECASE to intent-sdlc.py

**File:** `hooks/intent-sdlc.py`

**AC5:** Add `re.IGNORECASE` flag to all compiled patterns in PATTERNS dictionary (lines 82-83).

**Risk:** LOW — makes detection more robust.

---

### Task 6: Expand metachar guard in sdlc-permissions.py

**File:** `hooks/sdlc-permissions.py`

**AC6:** Add `{`, `}`, `!` to `_METACHARS` tuple (line 28).

**Risk:** LOW — security hardening.

---

### Task 7: Clarify timeout logic in auto-test.py

**File:** `hooks/auto-test.py`

**AC7:** Document that `auto_test_max_wait_s` path uses threading.Timer, not `timeout` variable. Consider making both paths consistent.

**Risk:** LOW — documentation/clarity improvement.

---

### Task 8: Filter files in session-cleanup.py

**File:** `hooks/session-cleanup.py`

**AC8:** Line 18: Add `if tmp_file.is_file()` before calling `.unlink()`.

**Risk:** LOW — defensive coding.

---

### Task 9: Add fallback in adr_summary.py

**File:** `hooks/adr_summary.py`

**AC9:** Add explicit default return at end of `_extract_decision()` if all fallbacks fail.

**Risk:** LOW — defensive coding.

---

## Test Plan

1. Run `make test-fast` after each task
2. Run `make test-unit` for full suite
3. Test with `qwen3-coder-next:cloud` model explicitly

---

## Notes

- All fixes must be non-breaking for existing Claude model users
- Each task should have unit tests
- Documentation updates in CLAUDE.md and README.md may be needed
