---
approved: false
approved_at: ~
backlog: backlog/impl-reviewer-risk-based.md
spec: specs/2026-03-24-impl-reviewer-risk-based-design.md
---

# impl-reviewer Risk-Based Invocation — Implementation Plan

**Goal:** Gate `@agent-impl-reviewer` invocation in `zie-implement.md` on a risk classification step so low-risk tasks skip the reviewer while high-risk tasks keep the existing review path.
**Architecture:** A single new "Risk Classification" block is inserted into `commands/zie-implement.md` immediately after the REFACTOR phase (current Step 5) and before the reviewer invocation (current Step 6). The block inspects two signals — task description keywords and files changed — and sets a `risk_level` of HIGH or LOW. Step 6 is then wrapped with an `if risk_level == HIGH` guard; LOW-risk tasks run `make test-unit` only. A `<!-- review: required -->` annotation in the task description overrides to HIGH regardless of other signals. No other files are touched; reviewer logic, checklist, and output format are unchanged.
**Tech Stack:** Markdown (command files), pytest (tests for string patterns)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Add risk classification block + gate reviewer on HIGH |
| Create | `tests/unit/test_impl_reviewer_risk_based.py` | Verify classification rules and reviewer gate present in command file |

---

## Task 1: Write tests for risk classification block (RED)
<!-- depends_on: none -->

**Acceptance Criteria:**
- Test file exists at `tests/unit/test_impl_reviewer_risk_based.py`
- Tests assert: HIGH-risk keywords present in command, LOW-risk keywords present in command, `review: required` override present, reviewer is gated on risk level (not invoked unconditionally), `make test-unit` still present on the LOW path

**Files:**
- Create: `tests/unit/test_impl_reviewer_risk_based.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_impl_reviewer_risk_based.py
  from pathlib import Path

  CMD = Path(__file__).parents[2] / "commands" / "zie-implement.md"


  def text():
      return CMD.read_text()


  class TestRiskClassificationBlockPresent:
      def test_command_file_exists(self):
          assert CMD.exists()

      def test_risk_classification_heading_present(self):
          assert "Risk Classification" in text(), \
              "zie-implement.md must contain a Risk Classification section"

      def test_risk_level_variable_defined(self):
          assert "risk_level" in text(), \
              "zie-implement.md must define a risk_level variable"

      def test_high_risk_label_present(self):
          assert "HIGH" in text(), \
              "zie-implement.md must reference the HIGH risk label"

      def test_low_risk_label_present(self):
          assert "LOW" in text(), \
              "zie-implement.md must reference the LOW risk label"


  class TestHighRiskSignals:
      def test_new_function_keyword(self):
          assert "new function" in text().lower() or "new function/class" in text().lower(), \
              "HIGH signals must mention new function/class"

      def test_changed_behavior_keyword(self):
          assert "changed behavior" in text().lower(), \
              "HIGH signals must mention changed behavior"

      def test_external_api_keyword(self):
          assert "external api" in text().lower(), \
              "HIGH signals must mention external API call"

      def test_security_sensitive_keyword(self):
          t = text().lower()
          assert "auth" in t or "file i/o" in t or "subprocess" in t, \
              "HIGH signals must mention auth/file-IO/subprocess"

      def test_review_required_annotation(self):
          assert "review: required" in text(), \
              "HIGH signals must mention review: required annotation override"


  class TestLowRiskSignals:
      def test_test_only_keyword(self):
          t = text().lower()
          assert "test only" in t or "test-only" in t or "add/edit test" in t, \
              "LOW signals must mention test-only tasks"

      def test_docs_config_keyword(self):
          t = text().lower()
          assert "docs" in t and "config" in t, \
              "LOW signals must mention docs/config changes"

      def test_rename_reformat_keyword(self):
          t = text().lower()
          assert "rename" in t or "reformat" in t, \
              "LOW signals must mention rename/reformat"

      def test_minor_addition_keyword(self):
          t = text().lower()
          assert "minor" in t, \
              "LOW signals must mention minor additions"


  class TestReviewerGate:
      def test_reviewer_gated_on_high(self):
          t = text()
          # The reviewer invocation must appear inside a conditional block
          # (risk_level == HIGH) — not unconditionally
          assert "risk_level" in t and "HIGH" in t and "@agent-impl-reviewer" in t, \
              "Reviewer invocation must be present and gated by risk_level"

      def test_low_path_runs_make_test_unit(self):
          t = text()
          # LOW path must still run the test suite
          assert "make test-unit" in t, \
              "make test-unit must remain present for the LOW path"

      def test_reviewer_not_invoked_unconditionally(self):
          t = text()
          lines = t.splitlines()
          # Find the line with @agent-impl-reviewer invocation
          reviewer_lines = [i for i, l in enumerate(lines) if "@agent-impl-reviewer" in l]
          assert reviewer_lines, "Reviewer invocation line must exist"
          # The conditional keyword "HIGH" must appear within 10 lines above any invocation
          for idx in reviewer_lines:
              context_block = "\n".join(lines[max(0, idx - 10):idx + 1])
              assert "HIGH" in context_block, \
                  f"@agent-impl-reviewer at line {idx+1} must be inside a HIGH risk guard"
  ```

  Run: `make test-unit` — must FAIL (Risk Classification block does not yet exist in `zie-implement.md`)

- [ ] **Step 2: Implement (GREEN)**

  No implementation in this task — tests must fail first to prove the RED state.
  Confirm `make test-unit` exits non-zero on the new test file.

- [ ] **Step 3: Refactor**

  No code to refactor. Verify test file has no syntax errors by running:
  ```bash
  python3 -m py_compile tests/unit/test_impl_reviewer_risk_based.py
  ```

---

## Task 2: Add Risk Classification block to `commands/zie-implement.md`
<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- A "Risk Classification" block appears in `zie-implement.md` between the REFACTOR phase (Step 5) and the reviewer invocation (Step 6)
- The block defines HIGH signals: new function/class, changed behavior, external API call, auth/file-IO/subprocess, `<!-- review: required -->` annotation
- The block defines LOW signals: add/edit test only, docs/config change, rename/reformat, minor field addition
- Step 6 (`@agent-impl-reviewer` spawn) is wrapped with `if risk_level == HIGH`
- LOW path explicitly runs `make test-unit` and skips the reviewer
- All other step content (steps 1-5, 7-8, post-loop section) is unchanged

**Files:**
- Modify: `commands/zie-implement.md`

- [ ] **Step 1: Write failing tests (RED)**

  Tests already written in Task 1 — they are still failing. No new tests needed.
  Run: `make test-unit` — confirm still FAILS on `test_impl_reviewer_risk_based.py`

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, replace the current Step 6 block (lines starting with `6. **Spawn async impl-reviewer**:`) with the following expanded block. The existing Step 6 content becomes the `if risk_level == HIGH` branch. Insert the new Risk Classification step as Step 6 and renumber the old Step 6 as Step 7 (and shift 7→8, 8→post-loop as needed).

  **Exact replacement — find this text:**
  ```
  6. **Spawn async impl-reviewer**:
  ```

  **Replace with:**
  ```markdown
  6. **Risk Classification** — Classify this task immediately after REFACTOR
     completes, before deciding whether to invoke the reviewer.

     **Signals → HIGH** (invoke reviewer):
     - Task description contains: new function/class, changed behavior,
       external API call, auth, file I/O, subprocess
     - Files changed include non-test production code (i.e., not solely
       `tests/` or `test_*.py` files)
     - Task description or plan task header contains `<!-- review: required -->`
       (forces HIGH regardless of other signals)

     **Signals → LOW** (skip reviewer):
     - Task is add/edit test only (all changed files are under `tests/` or
       match `test_*.py`)
     - Task is docs/config change only (changed files are `.md`, `.json`,
       `.toml`, `.yaml`, `.cfg`, `.ini`, or similar non-code files)
     - Task is rename/reformat only (no behavioral change — variable rename,
       formatting fix, import reorder)
     - Task is minor addition (new field in existing dict/list, extend existing
       list constant, update string constant — no new function/class)

     Set `risk_level = HIGH` or `risk_level = LOW` based on the above. When
     signals are mixed (e.g., test added alongside a new function), default to
     HIGH.

     **If `risk_level == LOW`:**
     - Run `make test-unit` to confirm tests still pass.
     - Print: `[risk: LOW] Skipping impl-reviewer — make test-unit passed.`
     - Proceed to Step 7 (task complete bookkeeping).

  7. **Spawn async impl-reviewer** (HIGH risk only):
     - Skip this step entirely if `risk_level == LOW`.
     - Invoke `@agent-impl-reviewer` (background: true):
       pass task description, **Acceptance Criteria** from plan task header,
       and list of files changed in this task.
     - Record returned handle in the pending-reviewers list:
       `{ task_id: <N>, reviewer_handle: <handle>, reviewer_status: pending }`
     - Do NOT block — proceed immediately to announce the next task.
     - **Deferred-check** (start of each task loop iteration): for each entry
       in the pending-reviewers list, poll handle → check `reviewer_status`:
       - `reviewer_status: pending` — still running; continue current task,
         check again at the next iteration.
       - `reviewer_status: approved` — clear entry from list; no action needed.
       - `reviewer_status: issues_found` — halt current task; surface reviewer
         feedback to human; apply fixes; re-run `make test-unit`; re-invoke
         `@agent-impl-reviewer` synchronously (blocking).
         Max 3 total iterations — background spawn counts as iteration 1.
         On APPROVED: clear entry from list; resume current task.
  ```

  After inserting the block, renumber all subsequent steps:
  - Old Step 7 → Step 8
  - Old Step 8 → Step 9

  Also update the **post-loop section** ("เมื่อทำครบทุก task"):
  - Step 0 "Final-wait for still-pending reviewers" — add a note:
    ```
    Note: LOW-risk tasks never add to the pending-reviewers list, so this
    wait step is a no-op for plans composed entirely of LOW-risk tasks.
    ```

  Run: `make test-unit` — must PASS (all assertions in `test_impl_reviewer_risk_based.py` satisfied)

- [ ] **Step 3: Refactor**

  Read the full modified `commands/zie-implement.md` from top to bottom. Verify:
  - Step numbers are consecutive (1 through 9 in the task loop, 0-4 in the post-loop section)
  - No duplicate step numbers
  - The REFACTOR phase (Step 5) content is unchanged
  - The post-loop "Final-wait" step 0 is intact with the LOW-risk note appended
  - `make test-unit` appears on the LOW path explicitly
  - `@agent-impl-reviewer` appears only inside the HIGH guard (Step 7)

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-implement.md tests/unit/test_impl_reviewer_risk_based.py && git commit -m "feat: impl-reviewer-risk-based"`*
