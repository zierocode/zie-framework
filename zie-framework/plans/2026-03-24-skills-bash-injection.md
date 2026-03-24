---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-bash-injection.md
spec: specs/2026-03-24-skills-bash-injection-design.md
---

# Skills !`cmd` Bash Injection for Live Context — Implementation Plan

**Goal:** Add `!`cmd`` bash injection placeholders to three command files (`zie-implement.md`, `zie-status.md`, `zie-retro.md`) so Claude receives live git and ROADMAP context with zero extra tool-call turns. Add pytest tests that assert the injection patterns are present and well-formed.

**Architecture:** Injections live entirely in command Markdown files. No hook changes, no skill file changes, no new Python modules. Each injection uses `||` fallback guards so a missing binary or empty repo never blocks command delivery. The `${CLAUDE_SKILL_DIR}` variable is used for `knowledge-hash.py` references in `zie-implement.md` to ensure the path resolves correctly regardless of CWD.

**Tech Stack:** Markdown (command files), Python 3.x / pytest (tests)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Add 3 bash injections to "ตรวจสอบก่อนเริ่ม" section |
| Modify | `commands/zie-status.md` | Add 2 bash injections to Steps section preamble |
| Modify | `commands/zie-retro.md` | Add 2 bash injections to "ตรวจสอบก่อนเริ่ม" section |
| Create | `tests/unit/test_skills_bash_injection.py` | Pytest assertions for all injection patterns |

---

## Task 1: Add bash injections to `zie-implement.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Three `!`cmd`` injection lines appear at the top of the "ตรวจสอบก่อนเริ่ม" section, before step 1
- `git log -5 --oneline` injection is present
- `git status --short` injection is present (replaces the explicit `git status --short` bash blocks in step 5 and the end-of-feature commit review — those blocks are updated to reference the already-injected value)
- `python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now` injection is present with `2>/dev/null || echo "knowledge-hash: unavailable"` fallback
- All injections complete in under 500 ms (bounded: 5 log lines, short index scan, local script)
- `make test-unit` passes after change

**Files:**
- Modify: `commands/zie-implement.md`
- Modify: `tests/unit/test_skills_bash_injection.py` (created in Task 4, referenced here for context)

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_skills_bash_injection.py

  import re
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"

  class TestZieImplementInjections:
      def setup_method(self):
          self.content = (COMMANDS_DIR / "zie-implement.md").read_text()

      def test_git_log_injection_present(self):
          assert "!`git log -5 --oneline`" in self.content

      def test_git_status_injection_present(self):
          assert "!`git status --short`" in self.content

      def test_knowledge_hash_injection_present(self):
          assert "!`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now" in self.content

      def test_knowledge_hash_injection_has_fallback(self):
          assert (
              "2>/dev/null || echo \"knowledge-hash: unavailable\"`" in self.content
              or "2>/dev/null || echo 'knowledge-hash: unavailable'`" in self.content
          )

      def test_claude_skill_dir_used_for_script_path(self):
          assert "${CLAUDE_SKILL_DIR}" in self.content
  ```

  Run: `make test-unit` — must FAIL (injections not yet present)

- [ ] **Step 2: Add injections to `zie-implement.md` (GREEN)**

  Insert the following block immediately after the `## ตรวจสอบก่อนเริ่ม` heading line and before the existing step 1 paragraph:

  ```markdown
  **Live context (injected at command load):**

  Recent commits:
  !`git log -5 --oneline`

  Working tree:
  !`git status --short`

  Knowledge hash:
  !`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now 2>/dev/null || echo "knowledge-hash: unavailable"`
  ```

  Then update the two existing explicit `git status --short` bash blocks:

  - **Step 5** — replace the fenced bash block:
    ```bash
    git status --short
    ```
    with the prose reference:
    ```
    (see "Working tree" snapshot injected above)
    ```

  - **End-of-feature commit review** ("Review what will be committed") — replace the fenced bash block:
    ```bash
    git status --short
    ```
    with:
    ```
    (see "Working tree" snapshot injected at command load; re-run Bash if session is long-running)
    ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify no other explicit `git status --short` bash blocks remain in `zie-implement.md` that duplicate the injected value. Confirm injections appear as the first content block under `## ตรวจสอบก่อนเริ่ม`. Confirm prose reads naturally.

  Run: `make test-unit` — still PASS

---

## Task 2: Add bash injections to `zie-status.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Two `!`cmd`` injection lines appear at the top of the Steps section, before step 1
- `cat zie-framework/ROADMAP.md | head -30` injection is present
- `python3 hooks/knowledge-hash.py` injection is present with `2>/dev/null || echo "knowledge-hash: unavailable"` fallback
- The existing step 4 bash block (`python3 hooks/knowledge-hash.py`) is updated to reference the injected value instead of re-running the command
- `make test-unit` passes after change

**Files:**
- Modify: `commands/zie-status.md`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_skills_bash_injection.py — add new class

  class TestZieStatusInjections:
      def setup_method(self):
          self.content = (COMMANDS_DIR / "zie-status.md").read_text()

      def test_roadmap_head_injection_present(self):
          assert "!`cat zie-framework/ROADMAP.md | head -30`" in self.content

      def test_knowledge_hash_injection_present(self):
          assert "!`python3 hooks/knowledge-hash.py" in self.content

      def test_knowledge_hash_injection_has_fallback(self):
          assert (
              "2>/dev/null || echo \"knowledge-hash: unavailable\"`" in self.content
              or "2>/dev/null || echo 'knowledge-hash: unavailable'`" in self.content
          )

      def test_injections_precede_steps(self):
          inject_pos = self.content.find("!`cat zie-framework/ROADMAP.md")
          steps_pos = self.content.find("## Steps")
          assert inject_pos > steps_pos, "Injections must appear inside the Steps section"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Add injections to `zie-status.md` (GREEN)**

  Insert the following block immediately after the `## Steps` heading line and before the existing step 1 paragraph:

  ```markdown
  **Live context (injected at command load):**

  ROADMAP snapshot (first 30 lines):
  !`cat zie-framework/ROADMAP.md | head -30`

  Knowledge hash:
  !`python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"`
  ```

  Then update step 4 ("Check knowledge drift via Bash"):

  Replace the instruction to run `python3 hooks/knowledge-hash.py` as a fresh Bash call with a reference to the injected value:

  ```markdown
  4. **Check knowledge drift** — use the knowledge hash injected above (see
     "Knowledge hash" snapshot at top of Steps). No additional Bash call needed.
  ```

  Keep the comparison logic (equal → synced, differs → drift) unchanged — only remove the redundant subprocess invocation.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm `python3 hooks/knowledge-hash.py` no longer appears as a fenced bash block in step 4. Confirm both injections appear as the first content block under `## Steps`. Confirm the step 4 drift-check logic is fully preserved.

  Run: `make test-unit` — still PASS

---

## Task 3: Add bash injections to `zie-retro.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Two `!`cmd`` injection lines appear at the top of the "ตรวจสอบก่อนเริ่ม" section, before step 1
- `git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline` injection is present
- `git log -20 --oneline` injection is present
- The existing step 4 prose block that instructs Claude to run those two git commands is updated to reference the injected values
- No-tag fallback (`git rev-list --max-parents=0 HEAD`) is part of the injection so repos without tags always produce a valid log range
- `make test-unit` passes after change

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_skills_bash_injection.py — add new class

  class TestZieRetroInjections:
      def setup_method(self):
          self.content = (COMMANDS_DIR / "zie-retro.md").read_text()

      def test_commits_since_tag_injection_present(self):
          assert (
              "!`git log $(git describe --tags --abbrev=0 2>/dev/null || "
              "git rev-list --max-parents=0 HEAD)..HEAD --oneline`"
          ) in self.content

      def test_recent_activity_injection_present(self):
          assert "!`git log -20 --oneline`" in self.content

      def test_no_tag_fallback_present(self):
          assert "git rev-list --max-parents=0 HEAD" in self.content

      def test_injections_in_preflight_section(self):
          inject_pos = self.content.find("!`git log $(git describe")
          preflight_pos = self.content.find("## ตรวจสอบก่อนเริ่ม")
          steps_pos = self.content.find("## Steps")
          assert preflight_pos < inject_pos < steps_pos, (
              "Injections must appear inside ตรวจสอบก่อนเริ่ม, before Steps"
          )
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Add injections to `zie-retro.md` (GREEN)**

  Insert the following block immediately after the `## ตรวจสอบก่อนเริ่ม` heading line and before the existing step 1 paragraph:

  ```markdown
  **Live context (injected at command load):**

  Commits since last tag:
  !`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`

  Recent activity window:
  !`git log -20 --oneline`
  ```

  Then update the existing step 4 git context block. Replace the prose that tells Claude to run:
  ```
  git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list
    --max-parents=0 HEAD)..HEAD --oneline
  git log -20 --oneline
  ```
  with a reference:
  ```markdown
  4. Git context is available in the injected snapshots above ("Commits since last
     tag" and "Recent activity window"). No additional Bash call needed.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm the two raw git log commands no longer appear as explicit Bash instructions in step 4. Confirm both injections are the first content under `## ตรวจสอบก่อนเริ่ม`. Confirm all other pre-flight steps (read `.config`, read `ROADMAP.md`) are unchanged.

  Run: `make test-unit` — still PASS

---

## Task 4: Add tests for injection patterns

<!-- depends_on: Task 1, Task 2, Task 3 -->

**Acceptance Criteria:**
- `tests/unit/test_skills_bash_injection.py` exists and covers all three command files
- Each command file has at least one test per injection (presence + fallback guard where applicable)
- `${CLAUDE_SKILL_DIR}` usage is verified for `zie-implement.md`
- Positional test verifies injections appear in the correct section of each command file
- All tests pass under `make test-unit`
- No network calls or subprocess execution in tests — assertions are pure string/regex checks on file content

**Files:**
- Create: `tests/unit/test_skills_bash_injection.py`

- [ ] **Step 1: Confirm RED baseline**

  Before Tasks 1–3 are applied, running `make test-unit` must show all tests in `test_skills_bash_injection.py` failing. This is the RED baseline confirming the test file is wired into the test suite.

  Verify `tests/unit/test_skills_bash_injection.py` is discovered by pytest:
  ```bash
  python3 -m pytest tests/unit/test_skills_bash_injection.py --collect-only
  ```
  Expected: all test IDs listed, no import errors.

- [ ] **Step 2: Assemble the full test file (GREEN)**

  The complete `tests/unit/test_skills_bash_injection.py` after Tasks 1–3 are done:

  ```python
  """
  Tests that bash injection patterns are present in zie-* command files.
  All assertions are pure string checks — no subprocess execution.
  """
  import pytest
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  class TestZieImplementInjections:
      def setup_method(self):
          self.content = (COMMANDS_DIR / "zie-implement.md").read_text()

      def test_git_log_injection_present(self):
          assert "!`git log -5 --oneline`" in self.content

      def test_git_status_injection_present(self):
          assert "!`git status --short`" in self.content

      def test_knowledge_hash_injection_present(self):
          assert (
              "!`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now"
              in self.content
          )

      def test_knowledge_hash_injection_has_fallback(self):
          assert (
              '2>/dev/null || echo "knowledge-hash: unavailable"`' in self.content
              or "2>/dev/null || echo 'knowledge-hash: unavailable'`" in self.content
          )

      def test_claude_skill_dir_used_for_script_path(self):
          assert "${CLAUDE_SKILL_DIR}" in self.content

      def test_injections_in_preflight_section(self):
          inject_pos = self.content.find("!`git log -5 --oneline`")
          preflight_pos = self.content.find("## ตรวจสอบก่อนเริ่ม")
          steps_pos = self.content.find("## Steps")
          assert preflight_pos < inject_pos < steps_pos, (
              "git log injection must appear inside ตรวจสอบก่อนเริ่ม, before Steps"
          )


  class TestZieStatusInjections:
      def setup_method(self):
          self.content = (COMMANDS_DIR / "zie-status.md").read_text()

      def test_roadmap_head_injection_present(self):
          assert "!`cat zie-framework/ROADMAP.md | head -30`" in self.content

      def test_knowledge_hash_injection_present(self):
          assert "!`python3 hooks/knowledge-hash.py" in self.content

      def test_knowledge_hash_injection_has_fallback(self):
          assert (
              '2>/dev/null || echo "knowledge-hash: unavailable"`' in self.content
              or "2>/dev/null || echo 'knowledge-hash: unavailable'`" in self.content
          )

      def test_injections_precede_first_step(self):
          inject_pos = self.content.find("!`cat zie-framework/ROADMAP.md")
          steps_pos = self.content.find("## Steps")
          # injections must be after ## Steps heading but before step 1
          step1_pos = self.content.find("\n1. **Check initialization**")
          assert steps_pos < inject_pos < step1_pos, (
              "ROADMAP injection must appear inside Steps section, before step 1"
          )


  class TestZieRetroInjections:
      def setup_method(self):
          self.content = (COMMANDS_DIR / "zie-retro.md").read_text()

      def test_commits_since_tag_injection_present(self):
          expected = (
              "!`git log $(git describe --tags --abbrev=0 2>/dev/null || "
              "git rev-list --max-parents=0 HEAD)..HEAD --oneline`"
          )
          assert expected in self.content

      def test_recent_activity_injection_present(self):
          assert "!`git log -20 --oneline`" in self.content

      def test_no_tag_fallback_present(self):
          assert "git rev-list --max-parents=0 HEAD" in self.content

      def test_injections_in_preflight_section(self):
          inject_pos = self.content.find("!`git log $(git describe")
          preflight_pos = self.content.find("## ตรวจสอบก่อนเริ่ม")
          steps_pos = self.content.find("## Steps")
          assert preflight_pos < inject_pos < steps_pos, (
              "Retro injections must appear inside ตรวจสอบก่อนเริ่ม, before Steps"
          )


  class TestNoUnboundedInjections:
      """Guard: no injection command is unbounded (no bare `git log` without -N or range)."""

      def _injections(self, filename: str) -> list[str]:
          content = (COMMANDS_DIR / filename).read_text()
          import re
          return re.findall(r"!`([^`]+)`", content)

      def test_implement_injections_are_bounded(self):
          for cmd in self._injections("zie-implement.md"):
              if "git log" in cmd:
                  assert (
                      "-5" in cmd or "-20" in cmd or "..HEAD" in cmd
                  ), f"Unbounded git log in zie-implement.md: {cmd}"

      def test_status_injections_are_bounded(self):
          for cmd in self._injections("zie-status.md"):
              if "cat" in cmd:
                  assert "head -30" in cmd, f"Unbounded cat in zie-status.md: {cmd}"

      def test_retro_injections_are_bounded(self):
          for cmd in self._injections("zie-retro.md"):
              if "git log" in cmd and "describe" not in cmd:
                  assert "-20" in cmd or "..HEAD" in cmd, (
                      f"Unbounded git log in zie-retro.md: {cmd}"
                  )
  ```

  Run: `make test-unit` — must PASS (all Tasks 1–3 complete)

- [ ] **Step 3: Refactor**

  Review test class names and assertions for clarity. Confirm `COMMANDS_DIR` path resolution is correct from `tests/unit/`. Confirm no test imports subprocess, requests, or any I/O beyond `Path.read_text()`.

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-implement.md commands/zie-status.md commands/zie-retro.md tests/unit/test_skills_bash_injection.py && git commit -m "feat: bash injection for live context in zie-implement, zie-status, zie-retro"`*
