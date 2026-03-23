---
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-fix-safety-hook.md
spec: specs/2026-03-23-audit-fix-safety-hook-design.md
---

# Plan: Safety Hook Fix

**Spec:** specs/2026-03-23-audit-fix-safety-hook-design.md
**Effort:** XS
**Test runner:** pytest

## Tasks

### Task 1 — Update block-case test assertions to expect returncode 2
**RED:** Change all `assert r.returncode == 1` in `TestSafetyCheckBlocks` and the
`test_force_with_lease_is_blocked` test in `TestSafetyCheckWarns` to
`assert r.returncode == 2`. Run `make test-unit` — these 8 tests now fail because
`safety-check.py` still exits with 1.

**GREEN:** No implementation change yet — tests are intentionally red. This task is
complete when the failing assertions are committed and CI is red on exactly those 8
tests.

**REFACTOR:** Confirm no other test file references `returncode == 1` for block cases.

---

### Task 2 — Fix exit code: sys.exit(1) → sys.exit(2) in safety-check.py
**RED:** (Inherited from Task 1 — the 8 block-case tests are already failing.)

**GREEN:** In `hooks/safety-check.py` line 59, change:
```python
sys.exit(1)  # Non-zero exit blocks the tool call (if Claude Code honors it)
```
to:
```python
sys.exit(2)  # exit(2) is the PreToolUse block signal per Claude Code protocol
```
Run `make test-unit` — all 8 previously-failing block tests now pass.

**REFACTOR:** Remove the parenthetical comment `(if Claude Code honors it)` — it is
now factually incorrect. The new comment should be authoritative.

---

### Task 3 — Remove dead WARNS entry and harden rm -rf ./ pattern
**RED:** Add two new tests to `TestSafetyCheckBlocks`:
- `test_rm_rf_dotslash_is_blocked`: calls `run_hook("Bash", "rm -rf ./")`, asserts
  `returncode == 2` and `"BLOCKED" in r.stdout`.
- `test_force_with_lease_warn_entry_absent`: structural test — read
  `hooks/safety-check.py` source and assert the string
  `"--force-with-lease"` does not appear in the `WARNS` list (use `ast` or plain
  string inspection of the file).

Run `make test-unit` — both new tests fail.

**GREEN:**
1. In `hooks/safety-check.py`, extend the existing `rm -rf .` BLOCKS pattern from:
   ```python
   (r"rm\s+-rf\s+\.", "rm -rf . blocked — use explicit paths"),
   ```
   to cover the trailing-slash variant. The simplest approach: the existing `\.`
   pattern already matches `rm -rf ./` because `.` precedes `/`. Verify with a quick
   `re.search` call — if it already matches, the `rm -rf ./` test passes with no
   regex change needed, and only the dead-entry removal remains.
2. In `WARNS`, delete the entire `--force-with-lease` tuple (lines 47–48 in current
   source). It is unreachable: `git push --force-with-lease` matches the
   `--force\b` BLOCKS pattern first.

Run `make test-unit` — both new tests pass; `test_force_with_lease_is_blocked`
continues to pass (it still hits BLOCKS).

**REFACTOR:** Confirm `WARNS` list now has exactly 2 entries. Add a brief inline
comment above `WARNS` noting that patterns shadowed by `BLOCKS` must not be
duplicated here.

---

### Task 4 — Remove hardcoded URLs and add https:// validation in session-learn.py and wip-checkpoint.py
**RED:** Add tests to the **existing** test files (NOT a new file):
- In `tests/unit/test_hooks_session_learn.py`: add
  `test_exits_zero_with_http_scheme_url` — runs `session-learn.py` with
  `ZIE_MEMORY_API_KEY=testkey` and `ZIE_MEMORY_API_URL=http://evil.example.com`,
  asserts `returncode == 0` (guard triggers clean exit, no crash, no HTTP attempt).
- In `tests/unit/test_hooks_wip_checkpoint.py`: add
  `test_exits_zero_with_http_scheme_url` — same pattern for `wip-checkpoint.py`.

The tests verify that a non-https URL causes clean exit (`returncode == 0` + no output).
Since `urllib.request` would raise `ValueError` or connect on http://, the absence of
crash output confirms the guard fires before the HTTP call.

Run `make test-unit` — tests fail because current code has hardcoded https default
and no scheme guard.

**GREEN:**
In `hooks/session-learn.py`:
1. Change line 15:
   ```python
   api_url = os.environ.get("ZIE_MEMORY_API_URL", "https://memory.zie-agent.cloud")
   ```
   to:
   ```python
   api_url = os.environ.get("ZIE_MEMORY_API_URL", "")
   ```
2. After the existing `if not api_key: sys.exit(0)` guard, add:
   ```python
   if not api_url.startswith("https://"):
       sys.exit(0)
   ```

In `hooks/wip-checkpoint.py`:
1. Change line 20:
   ```python
   api_url = os.environ.get("ZIE_MEMORY_API_URL", "https://memory.zie-agent.cloud")
   ```
   to:
   ```python
   api_url = os.environ.get("ZIE_MEMORY_API_URL", "")
   ```
2. After the existing `if not api_key: sys.exit(0)` guard, add:
   ```python
   if not api_url.startswith("https://"):
       sys.exit(0)
   ```

Run `make test-unit` — all new URL-safety tests pass.

**REFACTOR:** Verify the guard order in both files is consistent: `api_key` check
first, then `api_url` scheme check. Confirm no other default URL strings remain in
either file with a grep.
