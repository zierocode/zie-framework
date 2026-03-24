---
approved: false
approved_at: ~
backlog: backlog/retro-next-active-loop.md
spec: specs/2026-03-24-retro-next-active-loop-design.md
---

# Retro → Next Active Loop — Implementation Plan

**Goal:** Add a "Suggest next" final step to `commands/zie-retro.md` that reads the Next lane of ROADMAP.md after retro completes, ranks candidates by priority then retro-theme alignment, and prints the top 1–3 with a `/zie-plan <slug>` prompt. Output is advisory only — nothing is auto-started.
**Architecture:** Single markdown edit to `commands/zie-retro.md`. No new files, no new hooks, no new tests beyond the text-content assertions.
**Tech Stack:** Markdown (command definition), pytest (Path.read_text assertions)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-retro.md` | Add "Suggest next" step after the สรุปผล section |
| Create | `tests/unit/test_retro_next_active_loop.py` | Assert step present, /zie-plan prompt present, empty-backlog fallback present |

---

## Task 1: Add "Suggest next" step to `commands/zie-retro.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-retro.md` contains a "Suggest next" step heading
- The step reads the Next lane of ROADMAP.md
- Ranking rule is documented: Critical > High > Medium, then retro-theme alignment
- Output prints top 1–3 candidates each with `/zie-plan <slug> to start`
- Graceful fallback when Next lane is empty: "Backlog is empty — add items with /zie-backlog"
- All existing steps and output format are unchanged

**Files:**
- Modify: `commands/zie-retro.md`
- Create: `tests/unit/test_retro_next_active_loop.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_retro_next_active_loop.py
  from pathlib import Path

  RETRO_CMD = Path(__file__).parents[2] / "commands" / "zie-retro.md"


  def _text() -> str:
      return RETRO_CMD.read_text()


  class TestRetroNextActiveLoop:
      def test_suggest_next_step_present(self):
          assert "Suggest next" in _text(), \
              "zie-retro.md must contain a 'Suggest next' step"

      def test_zie_plan_prompt_present(self):
          assert "/zie-plan" in _text(), \
              "zie-retro.md must contain a '/zie-plan' prompt in the Suggest next step"

      def test_empty_backlog_fallback_present(self):
          assert "/zie-backlog" in _text(), \
              "zie-retro.md must contain the empty-backlog fallback referencing /zie-backlog"
  ```

  Run: `make test-unit` — must FAIL (step not yet in `zie-retro.md`)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-retro.md`, append the following section after the `### สรุปผล` block (after the closing ` ``` ` of the summary print block, before the `## Notes` section):

  ```markdown
  ### Suggest next

  After printing the retrospective summary, read `zie-framework/ROADMAP.md` and
  extract all items in the **Next** lane.

  **Ranking order:**
  1. Priority: Critical first, then High, then Medium, then unlabelled.
  2. Retro-theme alignment: items whose title or description overlaps with pain
     points or themes identified in the retro write-up rank higher within the
     same priority tier.

  **Output — items found (print top 1–3):**

  ```text
  Suggested next
  ──────────────────────────────────────────
  1. <slug> — <title> [<priority>]
     Run: /zie-plan <slug> to start

  2. <slug> — <title> [<priority>]
     Run: /zie-plan <slug> to start

  3. <slug> — <title> [<priority>]
     Run: /zie-plan <slug> to start
  ──────────────────────────────────────────
  ```

  **Output — Next lane is empty:**

  ```text
  Backlog is empty — add items with /zie-backlog
  ```

  This step is advisory only. Nothing is automatically started.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full `commands/zie-retro.md` and confirm:
  - All existing sections (`ตรวจสอบก่อนเริ่ม`, `รวบรวม context`, `วิเคราะห์และสรุป`,
    `บันทึก ADRs`, `อัปเดต project knowledge`, `อัปเดต ROADMAP`, `บันทึกสู่ brain`,
    `สรุปผล`) are unchanged.
  - `## Notes` block follows immediately after `### Suggest next`.
  - Frontmatter (`allowed-tools`, `model`, `effort`) is unchanged.

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-retro.md tests/unit/test_retro_next_active_loop.py && git commit -m "feat: retro-next-active-loop"`*
