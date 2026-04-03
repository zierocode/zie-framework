# Qwen3-coder-next Deep Review — Hook & Compatibility Issues

## Problem

Deep review of zie-framework identified 10 issues when used with the `qwen3-coder-next:cloud` model. These range from critical bugs that block execution to code quality improvements.

## Motivation

Zie runs Claude with `qwen3-coder-next:cloud` model. The framework was designed and tested primarily with Claude models. This review identifies compatibility issues that cause errors or unexpected behavior.

## Rough Scope

**Critical fixes (P1 - must fix before using with Qwen):**
- hooks.json syntax errors (`async: true` is invalid)
- safety_check_agent.py assumes `claude` CLI exists
- symlink handling in session-resume.py

**High priority (P2 - fix before production):**
- knowledge-hash.py EXCLUDE_PATHS logic bug
- intent-sdlc.py missing case-insensitive matching
- sdlc-permissions.py incomplete metachar guard

**Low priority (P3 - optional improvements):**
- auto-test.py timeout calculation confusion
- session-cleanup.py glob filtering
- adr_summary.py error handling

---

## Issues

### Issue #1: Invalid "async" key in hooks.json (CRITICAL)

**File:** `hooks/hooks.json`

**Problem:** Uses `"async": true` for Stop hooks, but this is not a valid key in Claude Code hook protocol. Should be `"background": true`.

**Affected hooks:**
- `session-learn.py` (line 130-131)
- `session-cleanup.py` (line 135-136)  
- `subagent-stop.py` (line 156-158)

**Fix:** Replace `"async": true` → `"background": true`

---

### Issue #2: safety_check_agent.py requires `claude` CLI (CRITICAL)

**File:** `hooks/safety_check_agent.py`

**Problem:** Line 58 uses `subprocess.run(["claude", "--print", prompt])` but `claude` CLI may not exist when using other models.

**Fix:** 
1. Check if `claude` CLI exists before using it
2. Fall back to regex-only mode if not available
3. Log warning when falling back

---

### Issue #3: Symlink handling in session-resume.py (HIGH)

**File:** `hooks/session-resume.py`

**Problem:** Lines 109-116 print warning for symlink but continue writing. Should exit immediately.

**Fix:** Add `sys.exit(0)` after warning, before the `else:` block.

---

### Issue #4: shlex.quote can produce overly long commands (MEDIUM)

**File:** `hooks/input-sanitizer.py`

**Problem:** Line 113 wraps commands with `shlex.quote()`. If original command is very long, the wrapped command may exceed shell limits.

**Fix:** Check command length before wrapping, skip confirmation for very long commands (>2048 chars).

---

### Issue #5: EXCLUDE_PATHS uses wrong logic (MEDIUM)

**File:** `hooks/knowledge-hash.py`

**Problem:** Line 44 uses `any(ex in p.parts for ex in EXCLUDE)` but `EXCLUDE_PATHS` contains strings like `'zie-framework/plans/archive'` which won't match path parts correctly.

**Fix:** Use `str(p.relative_to(root))` for comparison instead of `p.parts`.

---

### Issue #6: intent-sdlc.py missing case-insensitive regex (MEDIUM)

**File:** `hooks/intent-sdlc.py`

**Problem:** PATTERNS dictionary (lines 28-78) doesn't use `re.IGNORECASE`, so uppercase commands may not be detected.

**Fix:** Add `re.IGNORECASE` flag to compiled patterns or lowercase input before matching.

---

### Issue #7: sdlc-permissions.py incomplete metachar guard (MEDIUM)

**File:** `hooks/sdlc-permissions.py`

**Problem:** Line 28 `_METACHARS = (";", "&&", "||", "|", "`", "$(")` doesn't block `{}` or `!` which can be used for command substitution in zsh.

**Fix:** Add `{`, `}`, `!` to the metachar list.

---

### Issue #8: auto-test.py timeout calculation confusing (LOW)

**File:** `hooks/auto-test.py`

**Problem:** Line 116 computes `timeout = auto_test_timeout_ms // 1000` but this value is only used in the `subprocess.run` fallback path, not the `threading.Timer` path.

**Fix:** Clarify the logic or use consistent timeout for both paths.

---

### Issue #9: session-cleanup.py glob too broad (LOW)

**File:** `hooks/session-cleanup.py`

**Problem:** Line 18 uses `Path(tempfile.gettempdir()).glob(f"zie-{safe_project}-*")` without filtering by type, potentially matching unrelated files.

**Fix:** Filter by `p.is_file()` before calling `.unlink()`.

---

### Issue #10: adr_summary.py missing fallback (LOW)

**File:** `hooks/adr_summary.py`

**Problem:** `_extract_decision()` has fallbacks but they're in a complex nested structure. If all fallbacks fail, may return empty string.

**Fix:** Add explicit assertion or default value at the end.

---

## ขั้นตอนถัดไป

1. Create backlog items for P1 issues
2. Create backlog items for P2 issues
3. Schedule P3 improvements for later
4. Update ROADMAP.md Next section with these items
5. Run `/zie-spec` to write specs for critical issues
