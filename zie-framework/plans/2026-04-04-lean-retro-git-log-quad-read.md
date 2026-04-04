---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-retro-git-log-quad-read.md
---

# Lean Retro Git Log Quad-Read — Implementation Plan

**Goal:** Reduce `commands/retro.md` git log reads from 4 to 1 by consolidating the two bang injections and removing two mid-flow Bash subprocess calls.

**Architecture:** Apply ADR-052 bind-once discipline: one `!git log --oneline -50` bang at command load binds as `git_log_raw`; all downstream sections (self-tuning step, docs-sync guard) reference `git_log_raw` instead of spawning new subprocesses.

**Tech Stack:** Markdown prose (commands/retro.md), pytest structural tests.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/retro.md` | Consolidate two bangs → one; remove self-tuning Bash call; remove docs-sync Bash call; add `git_log_raw` bind in pre-flight |
| Modify | `tests/unit/test_skills_bash_injection.py` | Update `test_recent_activity_injection_present` to match new single bang (`-50`) |

---

## Task 1 — Consolidate bang injections + bind `git_log_raw` in pre-flight

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/retro.md` has exactly one `!git log` bang in the "ตรวจสอบก่อนเริ่ม" section (the `--oneline -50` injection).
- The old `!git log --oneline` (bare, no `-N`) and `!git log -20 --oneline` bangs are removed.
- Pre-flight step 4 binds `git_log_raw` from the injected output and says "no Bash needed".

**Files:**
- Modify: `commands/retro.md`

- [ ] **Step 1: Write failing test (RED)**

  Add to `tests/unit/test_skills_bash_injection.py` inside `TestZieRetroInjections`:

  ```python
  def test_single_git_log_bang_only(self):
      """Only one !git log bang allowed — the -50 injection."""
      import re
      bangs = re.findall(r"!`git log[^`]+`", self.content)
      git_log_bangs = [b for b in bangs if "git describe" not in b]
      assert len(git_log_bangs) == 1, (
          f"Expected 1 git log bang (not commits-since-tag), found {len(git_log_bangs)}: {git_log_bangs}"
      )
      assert "-50" in git_log_bangs[0], (
          f"The single git log bang must use -50, got: {git_log_bangs[0]}"
      )
  ```

  Also update the existing `test_recent_activity_injection_present` (will fail after edit):
  ```python
  def test_recent_activity_injection_present(self):
      assert "!`git log -50 --oneline`" in self.content
  ```

  Run: `make test-unit` — must FAIL (test_single_git_log_bang_only and test_recent_activity_injection_present both fail against current retro.md)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/retro.md`, replace the "ตรวจสอบก่อนเริ่ม" banner section:

  **REMOVE these two lines:**
  ```
  !`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`

  Recent activity window:
  !`git log -20 --oneline`
  ```

  **REPLACE WITH:**
  ```
  Commits since last tag:
  !`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`

  Recent activity (last 50 commits — bound as `git_log_raw` at pre-flight):
  !`git log -50 --oneline`
  ```

  Then update pre-flight step 4 (currently: `Print: "Analyzing git log..." — git context already injected above, no Bash needed.`):

  **REPLACE WITH:**
  ```
  4. Bind `git_log_raw` — the `!git log -50 --oneline` bang output injected above. Used by self-tuning and docs-sync guard — no Bash call needed.
     Print: "Analyzing git log..." — git context already injected above, no Bash needed.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify both the commits-since-tag bang and the new -50 bang are cleanly separated with clear labels. Confirm `test_commits_since_tag_injection_present` and `test_no_tag_fallback_present` still pass.

  Run: `make test-unit` — still PASS

---

## Task 2 — Remove `git log --oneline -50` Bash call in self-tuning step

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- The self-tuning step in `commands/retro.md` references `git_log_raw` instead of `git log --oneline -50`.
- No `Bash` call to `git log` appears in the self-tuning section.

**Files:**
- Modify: `commands/retro.md`

- [ ] **Step 1: Write failing test (RED)**

  Add to `tests/unit/test_skills_bash_injection.py` inside `TestZieRetroInjections`:

  ```python
  def test_self_tuning_uses_git_log_raw_not_bash(self):
      """Self-tuning step must reference git_log_raw, not spawn a Bash git log call."""
      # Find the self-tuning section
      start = self.content.find("Self-tuning proposals")
      end = self.content.find("### Auto-commit", start)
      if start == -1:
          pytest.skip("Self-tuning section not found")
      section = self.content[start:end] if end != -1 else self.content[start:]
      assert "git_log_raw" in section, (
          "Self-tuning step must reference git_log_raw (not spawn Bash git log)"
      )
      import re
      bash_git_log = re.findall(r"git log[^\n]*oneline", section)
      assert not bash_git_log, (
          f"Self-tuning section must not contain bare git log calls: {bash_git_log}"
      )
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/retro.md`, locate the Self-tuning proposals section. Replace:

  ```
  2. Scan `git log --oneline -50` for commits matching `RED` + a numeric day count (e.g. "RED phase stuck 3 days").
     Parse up to 5 RED cycle durations. If average > 3 days → propose `auto_test_max_wait_s: <current> → 30`.
  3. Check current `safety_check_mode`; if `"agent"` and no `"BLOCK"` found in `git log --oneline -20` →
     propose `safety_check_mode: "agent" → "regex"`.
  ```

  With:

  ```
  2. Scan `git_log_raw` (bound at pre-flight — no Bash needed) for commits matching `RED` + a numeric day count (e.g. "RED phase stuck 3 days").
     Parse up to 5 RED cycle durations. If average > 3 days → propose `auto_test_max_wait_s: <current> → 30`.
  3. Check current `safety_check_mode`; if `"agent"` and no `"BLOCK"` found in `git_log_raw` →
     propose `safety_check_mode: "agent" → "regex"`.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm the self-tuning prose is internally consistent: all git log references use `git_log_raw`.

  Run: `make test-unit` — still PASS

---

## Task 3 — Remove `git log -1 --format="%s"` Bash call in docs-sync guard

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- The docs-sync guard in `commands/retro.md` extracts the last commit subject from `git_log_raw` (first line) instead of spawning `git log -1 --format="%s"`.
- No `git log -1` call appears in `commands/retro.md`.

**Files:**
- Modify: `commands/retro.md`

- [ ] **Step 1: Write failing test (RED)**

  Add to `tests/unit/test_skills_bash_injection.py` inside `TestZieRetroInjections`:

  ```python
  def test_docs_sync_guard_uses_git_log_raw_not_bash(self):
      """Docs-sync skip guard must read from git_log_raw, not spawn git log -1."""
      assert "git log -1" not in self.content, (
          "retro.md must not use git log -1; extract last commit subject from git_log_raw instead"
      )
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `commands/retro.md`, locate the docs-sync skip guard. Replace:

  ```
  Skip guard: if `git log -1 --format="%s"` starts with `release:` → print `"Docs-sync: skipped (ran during release)"` and skip.
  ```

  With:

  ```
  Skip guard: if the first line of `git_log_raw` (bound at pre-flight) starts with a hash + space + `release:` → print `"Docs-sync: skipped (ran during release)"` and skip. No Bash call needed.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the docs-sync section prose is clear: `git_log_raw` first line → extract subject (strip leading hash + short sha prefix).

  Run: `make test-unit` — still PASS

---

## Task 4 — Final verify

<!-- depends_on: Task 2, Task 3 -->

**Acceptance Criteria:**
- All tests pass.
- No lint errors.
- `commands/retro.md` has exactly 1 non-commits-since-tag `!git log` bang.
- `commands/retro.md` has 0 mid-flow `git log` Bash calls (self-tuning + docs-sync both use `git_log_raw`).

**Files:** None (read-only verification)

- [ ] **Step 1: Run full test + lint**

  ```bash
  make test-unit
  make lint
  ```

  Expected: 0 failures, 0 lint errors.

- [ ] **Step 2: Spot-check retro.md**

  Manually verify:
  1. Banner: 2 bangs total — `git log $(git describe...)..HEAD` + `git log -50 --oneline`.
  2. Pre-flight step 4: binds `git_log_raw`.
  3. Self-tuning: references `git_log_raw` in steps 2 and 3.
  4. Docs-sync guard: references `git_log_raw` first line, no `git log -1`.

- [ ] **Step 3: Refactor (none needed)**

  No further cleanup required.

  Run: `make test-unit` — still PASS
