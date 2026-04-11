---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-retro-self-tuning-blocks-release.md
---

# Lean Retro — Self-Tuning Proposals Non-Blocking — Implementation Plan

**Goal:** Remove the interactive `"Apply?"` prompt from `/retro`'s self-tuning section so it never blocks the automated pipeline.
**Architecture:** Pure command-text edit — reorder the self-tuning section to the final printed step (after auto-commit, knowledge update, brain storage, archive prune, and suggest-next), strip the interactive wait, replace with a non-blocking advisory message, and add a `self_tuning_enabled` config gate. All logic in `utils_self_tuning.py` is left untouched; only the command orchestration and CLAUDE.md documentation change.
**Tech Stack:** Markdown (commands/retro.md, CLAUDE.md), Python pytest (test file).

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/retro.md` | Reorder self-tuning to final printed step; remove interactive wait; add `self_tuning_enabled` gate; replace with advisory message |
| Modify | `CLAUDE.md` | Add `self_tuning_enabled` row to Hook Configuration table |
| Modify | `tests/unit/test_retro_self_tuning.py` | Add tests for advisory message format, absence of interactive prompt, and `self_tuning_enabled: false` skip path |

## Task Sizing

3 tasks — S plan (single-session feature). Tasks 1 and 2 are independent (different files). Task 3 depends on Task 1 for the exact wording of the advisory message.

---

## Task 1: Rewrite self-tuning section in retro.md

**Acceptance Criteria:**
- The `### Self-tuning proposals` section appears as the final printed block in `/retro` — after Suggest next
- No interactive prompt (`"Apply?"` / `"Type 'apply'"`) appears anywhere in the section
- Advisory message format is: `[zie-framework] self-tuning: N proposal(s) — run /chore to apply. See self-tuning proposals above.`
- When `self_tuning_enabled: false` in `.config`, section prints `"Self-tuning: disabled"` and skips
- When `.config` is absent, self-tuning still runs (default `true`)

**Files:**
- Modify: `commands/retro.md`

- [ ] **Step 1: Write failing tests (RED)**
  Tests in Task 3 cover the command text — write them first (Task 3 depends_on Task 1, so sequence: write Task 3 tests → RED → implement Task 1 → GREEN).
  Run: `make test-unit` — must FAIL (tests reference advisory message text not yet in retro.md)

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/retro.md`:

  a. **Remove** the entire existing `### Self-tuning proposals` section (lines 106–125 in current file, positioned "After docs-sync verdict, before auto-commit").

  b. **Append** a new `### Self-tuning proposals (advisory)` section as the very last section, after `### Suggest next`:

  ```markdown
  ### Self-tuning proposals (advisory)

  After Suggest next — always the last printed block:

  1. Read `self_tuning_enabled` from `zie-framework/.config`. If key absent → treat as `true`. If `false` → print `"Self-tuning: disabled"` and skip this section entirely.
  2. Read `zie-framework/.config`. If `.config` absent → skip silently (default `true` but no config to scan).
  3. Scan `git log --oneline -50` for commits matching `RED` + a numeric day count (e.g. "RED phase stuck 3 days").
     Parse up to 5 RED cycle durations. If average > 3 days → propose `auto_test_max_wait_s: <current> → 30`.
  4. Check current `safety_check_mode`; if `"agent"` and no `"BLOCK"` found in `git log --oneline -20` →
     propose `safety_check_mode: "agent" → "regex"`.
  5. If no proposals → print `"Self-tuning: no changes proposed"` and stop.
  6. Otherwise print each proposal line:
     ```
     [zie-framework] Self-tuning proposals:
       <key>: <from_val> → <to_val>  (<reason>)
     ```
     Then print the advisory message:
     ```
     [zie-framework] self-tuning: N proposal(s) — run /chore to apply. See self-tuning proposals above.
     ```
  7. Do NOT wait for user input. Do NOT write to `.config`. Continue immediately.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify section ordering in retro.md: Pre-flight → Context → Compact summary → Retrospective inline → ADRs + ROADMAP → Done-rotation → Auto-commit → Knowledge update → Brain storage → Summary → Archive prune → Suggest next → Self-tuning proposals (advisory).
  Run: `make test-unit` — still PASS

---

## Task 2: Add self_tuning_enabled to CLAUDE.md Hook Configuration table

<!-- depends_on: none -->

**Acceptance Criteria:**
- `CLAUDE.md` Hook Configuration table contains a `self_tuning_enabled` row with correct default, values, and description

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test covers CLAUDE.md content — verification is manual. Proceed directly to implementation.

- [ ] **Step 2: Implement (GREEN)**

  In `CLAUDE.md`, add a new row to the Hook Configuration table (after the `compact_hint_threshold` row):

  ```markdown
  | `self_tuning_enabled` | `true` | `true`, `false` | When `false`, skip the self-tuning proposals section entirely in `/retro`. |
  ```

  Run: `make lint` — must PASS (markdown linting)

- [ ] **Step 3: Refactor**
  Confirm table alignment is consistent with existing rows.
  Run: `make lint` — still PASS

---

## Task 3: Add tests for advisory message format and self_tuning_enabled skip path

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Test asserts advisory message format matches `[zie-framework] self-tuning: N proposal(s) — run /chore to apply. See self-tuning proposals above.`
- Test asserts interactive prompt string (`"Apply?"` or `"Type 'apply'"`) is absent from `commands/retro.md`
- Test asserts that when `self_tuning_enabled: false`, section prints `"Self-tuning: disabled"` (checked via command text presence)
- Existing `test_retro_self_tuning.py` tests still pass

**Files:**
- Modify: `tests/unit/test_retro_self_tuning.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append to `tests/unit/test_retro_self_tuning.py`:

  ```python
  import re
  from pathlib import Path


  RETRO_MD = Path(__file__).parent.parent.parent / "commands" / "retro.md"


  class TestRetroCommandText:
      def test_no_interactive_apply_prompt(self):
          """Interactive 'Apply?' prompt must not appear in retro.md."""
          text = RETRO_MD.read_text()
          assert "Apply?" not in text
          assert 'Type "apply"' not in text
          assert "Type 'apply'" not in text

      def test_advisory_message_format_present(self):
          """Advisory message must appear in retro.md with correct format."""
          text = RETRO_MD.read_text()
          # Check the advisory pattern is present
          assert "run /chore to apply" in text
          assert "self-tuning proposals above" in text

      def test_self_tuning_enabled_false_skip_path_present(self):
          """retro.md must document the self_tuning_enabled: false skip path."""
          text = RETRO_MD.read_text()
          assert "self_tuning_enabled" in text
          assert "Self-tuning: disabled" in text

      def test_self_tuning_is_last_section(self):
          """Self-tuning section must appear after 'Suggest next' in retro.md."""
          text = RETRO_MD.read_text()
          suggest_idx = text.find("Suggest next")
          self_tuning_idx = text.find("Self-tuning proposals")
          assert suggest_idx != -1, "Suggest next section not found"
          assert self_tuning_idx != -1, "Self-tuning proposals section not found"
          assert self_tuning_idx > suggest_idx, (
              "Self-tuning proposals must appear after Suggest next"
          )
  ```

  Run: `make test-unit` — must FAIL (retro.md still has old interactive prompt)

- [ ] **Step 2: Implement (GREEN)**
  Task 1 must be complete. Once retro.md is updated, run:
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Review test class for clarity; ensure no duplication with existing `TestBuildTuningProposals`.
  Run: `make test-unit` — still PASS

---

## Execution Order

1. **Task 3 Step 1** — write failing tests first (RED)
2. **Task 1 Step 2** — implement retro.md changes (GREEN for Task 3)
3. **Task 2 Step 2** — add CLAUDE.md row (parallel-safe, independent)
4. Run `make test-unit` — full green
5. Run `make lint` — clean
