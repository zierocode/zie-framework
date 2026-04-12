---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-observability-health-command.md
---

# Lean Observability: Framework Health Section in /status — Implementation Plan

**Goal:** Add a "Framework Health" section to `/status` output that surfaces
safety_check_mode, zie-memory/playwright status, drift bypass count, and the
last 5 stop-failure log entries.

**Architecture:** `/status` is a pure-markdown command file — no Python code to
change. The implementation is limited to two files: `commands/status.md` (add
read instructions + print block) and `tests/unit/test_commands_status.py` (new
structural test file asserting the new section exists and is correctly specified).
Stopfailure-log path follows the same logic already used by `hooks/stopfailure-log.py`
via `project_tmp_path("failure-log", safe_project_name(cwd.name))`.

**Tech Stack:** Markdown (command file), Python 3.x / pytest (tests), existing
`hooks/utils_io.py` path constants.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/status.md` | Add stopfailure-log read to Step 2; add Framework Health section to Step 7 print block |
| Create | `tests/unit/test_commands_status.py` | Structural tests asserting Framework Health section is specified in status.md |

---

## Task 1: Update `commands/status.md` — read + render Framework Health

**Acceptance Criteria:**

- `commands/status.md` Step 2 instructs reading the stopfailure-log at
  `project_tmp_path("failure-log", safe_project_name(cwd.name))`
  i.e. `/tmp/zie-<sanitized-project-name>-failure-log`
- Step 7 print block contains a `**Framework Health**` section showing
  `safety_check_mode`, `zie-memory`, `playwright`, `Drift bypasses` rows
- Step 7 print block contains `**Stop failures (last 5):**` with instructions
  to tail the last 5 lines; fall back to "No stop failures recorded"
- Stop-failure log lines are clipped at 120 chars to comply with MD013
- Framework Health section appears after the Tests table and before "ขั้นตอนถัดไป"
- No new hooks, no new log files, no subprocess calls introduced

**Files:**

- Modify: `commands/status.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_commands_status.py
  # (Create this file — it tests the spec assertions, not the runtime)
  # Step 1 only asserts the CURRENT state — tests will FAIL until Task 2 writes
  # the actual content.
  from pathlib import Path
  import os

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  STATUS_CMD = Path(REPO_ROOT) / "commands" / "status.md"

  class TestStatusFrameworkHealthSection:
      def _src(self):
          return STATUS_CMD.read_text()

      def test_framework_health_heading_present(self):
          assert "Framework Health" in self._src(), \
              "status.md must include a Framework Health section"

      def test_safety_check_mode_row_present(self):
          assert "safety_check_mode" in self._src(), \
              "status.md must surface safety_check_mode in Framework Health"

      def test_zie_memory_row_present(self):
          src = self._src()
          assert "zie-memory" in src or "zie_memory" in src, \
              "status.md must surface zie-memory status in Framework Health"

      def test_playwright_row_present(self):
          assert "playwright" in self._src(), \
              "status.md must surface playwright status in Framework Health"

      def test_stop_failures_section_present(self):
          assert "Stop failures" in self._src(), \
              "status.md must include Stop failures subsection"

      def test_stopfailure_log_path_documented(self):
          src = self._src()
          assert "failure-log" in src, \
              "status.md must document the stopfailure-log path"

      def test_last_5_entries_instruction_present(self):
          src = self._src()
          assert "last 5" in src or "tail" in src, \
              "status.md must instruct tail/last-5 entries from stopfailure-log"

      def test_missing_log_fallback_documented(self):
          src = self._src()
          assert "No stop failures" in src, \
              "status.md must document 'No stop failures recorded' fallback"

      def test_line_truncation_documented(self):
          src = self._src()
          assert "120" in src, \
              "status.md must document 120-char truncation for MD013 compliance"
  ```

  Run: `make test-unit` — must **FAIL** (Framework Health not yet in status.md)

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/status.md`:

  **In Step 2** — add after the drift-log read instruction:

  ```markdown
     Read the stopfailure-log at
     `project_tmp_path("failure-log", safe_project_name(cwd.name))` →
     `/tmp/zie-<sanitized-project-name>-failure-log`.
     Tail last 5 non-empty lines. If file missing → use empty list.
     Clip each line at 120 chars.
  ```

  **In Step 7** — add after the Tests table and before the "ขั้นตอนถัดไป" block:

  ```markdown
     **Framework Health**

     | | |
     | --- | --- |
     | safety_check_mode | \<value from .config, default: regex> |
     | zie-memory | \<enabled \| disabled> |
     | playwright | \<enabled \| disabled> |
     | Drift bypasses | \<N> events |

     **Stop failures (last 5):**
     \<tail last 5 non-empty lines from failure-log, each clipped at 120 chars>
     — or — `No stop failures recorded` if file missing or empty
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  Review `commands/status.md` for:
  - Consistent table alignment (all Framework Health rows use the same `| | |` style)
  - "playwright" row label is lowercase (matches config key convention)
  - Section placement is correct: after Tests table, before "ขั้นตอนถัดไป"
  - No lines exceed 120 chars in the markdown itself (markdownlint MD013)

  Run: `make test-unit` — still **PASS**
  Run: `make lint` — must **PASS** (markdownlint)

---

## Task 2: Write structural tests for Framework Health

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `tests/unit/test_commands_status.py` exists and contains ≥8 structural assertions
- All 9 test methods pass with `make test-unit`
- Tests are pure file-read assertions — no subprocess, no tmp directory

**Files:**

- Create: `tests/unit/test_commands_status.py`

- [ ] **Step 1: Write failing tests (RED)**

  File already created in Task 1 Step 1. Verify it exists:

  ```bash
  ls tests/unit/test_commands_status.py
  ```

  Run: `make test-unit` — must show `test_commands_status` in output

- [ ] **Step 2: Implement (GREEN)**

  No additional implementation needed — tests were written in Task 1 Step 1
  and the command was updated in Task 1 Step 2.

  Run: `make test-unit` — all `TestStatusFrameworkHealthSection` tests must **PASS**

- [ ] **Step 3: Refactor**

  Review test file:
  - Each test has a clear docstring or inline comment
  - No duplicate assertions between test methods
  - Class name `TestStatusFrameworkHealthSection` matches file purpose

  Run: `make test-unit` — still **PASS**

---

## Commit

After both tasks pass:

```bash
git add commands/status.md tests/unit/test_commands_status.py
git commit -m "feat: lean-observability-health-command — add Framework Health section to /status"
```
