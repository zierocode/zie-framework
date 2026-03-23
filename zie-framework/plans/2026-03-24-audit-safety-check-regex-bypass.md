---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-safety-check-regex-bypass.md
spec: specs/2026-03-24-audit-safety-check-regex-bypass-design.md
---

# Safety-Check Regex Bypass — Implementation Plan

**Goal:** Normalize whitespace on `cmd` before pattern matching so extra spaces cannot bypass block patterns.
**Architecture:** Single-point fix in `hooks/safety-check.py` — replace `cmd = command.strip().lower()` with `cmd = re.sub(r'\s+', ' ', command.strip().lower())`. No new helpers, no new dependencies. Both `BLOCKS` and `WARNS` share the normalized `cmd` automatically.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/safety-check.py` | Normalize whitespace before pattern matching |
| Modify | `tests/unit/test_hooks_safety_check.py` | Add bypass-variant test cases |

---

## Task 1: Reject Whitespace-Padded Bypass Variants

**Acceptance Criteria:**
- `rm  -rf  ./` (double spaces) exits 2 with BLOCKED
- `rm  -rf  /` exits 2 with BLOCKED
- `rm  -rf  ~` exits 2 with BLOCKED
- `git push  origin  main` exits 2 with BLOCKED
- `git push -u  origin  main` exits 2 with BLOCKED
- `git  push  --force  origin  dev` exits 2 with BLOCKED
- All existing passing tests remain green

**Files:**
- Modify: `tests/unit/test_hooks_safety_check.py`
- Modify: `hooks/safety-check.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_hooks_safety_check.py
  # Inside class TestSafetyCheckBlocks:

  class TestSafetyCheckRegexBypass:
      """Whitespace bypass variants — must all be blocked after normalization."""

      def test_rm_rf_double_space_dot_is_blocked(self):
          r = run_hook("Bash", "rm  -rf  .")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_rm_rf_double_space_dotslash_is_blocked(self):
          r = run_hook("Bash", "rm  -rf  ./")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_rm_rf_double_space_root_is_blocked(self):
          r = run_hook("Bash", "rm  -rf  /")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_rm_rf_double_space_home_is_blocked(self):
          r = run_hook("Bash", "rm  -rf  ~")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_git_push_origin_main_double_space_is_blocked(self):
          r = run_hook("Bash", "git push  origin  main")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_git_push_u_origin_main_extra_space_is_blocked(self):
          r = run_hook("Bash", "git push -u  origin  main")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_git_push_force_double_space_is_blocked(self):
          r = run_hook("Bash", "git  push  --force  origin  dev")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_git_reset_hard_double_space_is_blocked(self):
          r = run_hook("Bash", "git  reset  --hard  HEAD~1")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout

      def test_multiline_rm_rf_is_blocked(self):
          r = run_hook("Bash", "rm\n-rf\n./")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout
  ```

  Run: `make test-unit` — must FAIL (all 9 new tests fail, returncode 0 instead of 2)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/safety-check.py, replace line 20:
  # BEFORE:
  cmd = command.strip().lower()

  # AFTER:
  cmd = re.sub(r'\s+', ' ', command.strip().lower())
  ```

  Full replacement — only that one line changes. The rest of the file is unchanged.

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No structural changes needed — the fix is already minimal and idiomatic.
  Verify the `BLOCKS` patterns that use `\s+` internally (`r"rm\s+-rf\s+..."`) still
  match correctly against the now-single-space-normalized `cmd`. They do because
  `\s+` matches one or more whitespace characters, including a single space.

  Run: `make test-unit` — still PASS

---

**Commit:** `git add hooks/safety-check.py tests/unit/test_hooks_safety_check.py && git commit -m "fix: audit-safety-check-regex-bypass — normalize whitespace before pattern match"`
