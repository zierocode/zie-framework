---
approved: false
approved_at: ~
backlog: backlog/implement-guidance-inline.md
spec: specs/2026-03-24-implement-guidance-inline-design.md
---

# Implement Loop — Inline Guidance + Parallel Tasks by Default — Implementation Plan

**Goal:** Remove per-task `Skill(zie-framework:tdd-loop)` and `Skill(zie-framework:test-pyramid)` invocations from `/zie-implement` — replacing them with a single inline guidance block printed once at session start. Invert parallelism default: tasks without `depends_on` run in parallel by default instead of requiring explicit annotation.
**Architecture:** Single file change — `commands/zie-implement.md`. No new files, no new skills, no new agents.
**Tech Stack:** Markdown (command definition), pytest (content assertions)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Remove per-task skill calls; add inline guidance block at session start; add parallel-by-default logic |
| Create | `tests/unit/test_implement_guidance_inline.py` | Assert guidance present, per-task Skill calls absent, tdd:deep conditional present, parallel-by-default logic present |

---

## Task 1: Inline guidance block

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-implement.md` contains an inline TDD guidance block printed once at session start (before the task loop)
- The block includes RED/GREEN/REFACTOR summary and test-pyramid decision rule inline
- `Skill(zie-framework:tdd-loop)` is NOT present as a per-task call in the normal task loop steps (steps 2–3)
- `Skill(zie-framework:test-pyramid)` is NOT present anywhere in the file
- `Skill(zie-framework:tdd-loop)` IS still present as a conditional invocation for the `tdd: deep` hint
- Unexpected test failures invoke `Skill(zie-framework:debug)` (existing `## เมื่อ test ล้มเหลว` section) — this satisfies the spirit of "help with unexpected failures"; the tdd-loop skill is NOT triggered on failure and that path is preserved as-is

**Files:**
- Modify: `commands/zie-implement.md`
- Create: `tests/unit/test_implement_guidance_inline.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_implement_guidance_inline.py
  from pathlib import Path

  CMD = Path(__file__).parents[2] / "commands" / "zie-implement.md"


  def read_cmd() -> str:
      return CMD.read_text()


  class TestInlineGuidanceBlock:
      def test_inline_tdd_guidance_present(self):
          text = read_cmd()
          assert "RED" in text and "GREEN" in text and "REFACTOR" in text, \
              "Inline TDD guidance block must contain RED, GREEN, REFACTOR"

      def test_inline_test_pyramid_rule_present(self):
          text = read_cmd()
          assert "unit" in text and "integration" in text and "e2e" in text, \
              "Inline test-pyramid rule must name unit, integration, and e2e"

      def test_per_task_tdd_loop_skill_absent(self):
          """The old per-task tdd-loop invocation line must not appear in the task loop body."""
          text = read_cmd()
          # Assert the specific old step 2 text is absent, not the bare skill name
          # (the skill name still legitimately appears in the tdd:deep conditional)
          assert 'Invoke `Skill(zie-framework:tdd-loop)` for RED/GREEN/REFACTOR guidance' not in text, \
              "Old per-task tdd-loop invocation line must not appear in zie-implement.md"

      def test_test_pyramid_skill_absent(self):
          text = read_cmd()
          assert "Skill(zie-framework:test-pyramid)" not in text, \
              "Skill(zie-framework:test-pyramid) must not appear anywhere in zie-implement.md"

      def test_tdd_deep_conditional_present(self):
          text = read_cmd()
          assert "tdd: deep" in text, \
              "Conditional Skill(tdd-loop) for tdd: deep hint must be present"
          assert "Skill(zie-framework:tdd-loop)" in text, \
              "Skill(zie-framework:tdd-loop) must still appear for tdd: deep path"
  ```

  Run: `make test-unit` — must FAIL (per-task Skill calls still present, inline block absent)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, make the following changes:

  **2a. Add inline TDD guidance block** — insert after the `### วิเคราะห์ dependency ระหว่าง tasks` section and before `## Steps`, as a new subsection:

  ```markdown
  ### TDD Guidance (printed once at session start)

  Print this block before starting the task loop — do not repeat per task:

  ```text
  TDD Cycle — RED → GREEN → REFACTOR
  - RED:     Write a failing test that captures the desired behavior. Run make test-unit to confirm it fails.
  - GREEN:   Write the minimum code to make the test pass. No speculation, no extras. Run make test-unit.
  - REFACTOR: Clean up — remove duplication, clarify names, simplify logic. Run make test-unit to confirm still passing.

  Test level selection:
  - unit        — isolated logic, pure functions, single-module behavior
  - integration — cross-module, file I/O, database, external config
  - e2e         — full UI flows, browser interactions, end-to-end user journeys

  If tdd: deep is set in the plan frontmatter, invoke Skill(zie-framework:tdd-loop) for each task instead of using this summary.
  ```
  ```

  **2b. Remove per-task Skill invocations** — in the `## Steps` / `### วนรอบ task จนครบ` section, replace steps 2 and 3:

  Before (step 2):
  ```markdown
  2. Invoke `Skill(zie-framework:tdd-loop)` for RED/GREEN/REFACTOR guidance.
     Skip only for pure documentation tasks (no code changes).

  3. **เขียน test ที่ล้มเหลวก่อน (RED)**
     Invoke `Skill(zie-framework:test-pyramid)` เพื่อเลือก test level (unit /
     integration / e2e) ที่เหมาะสม แล้วเขียน test ที่ capture behavior ที่ต้องการ
     — test ต้อง fail ก่อนเสมอ รัน `make test-unit` เพื่อยืนยัน
     ถ้า test ผ่านแล้ว → feature มีอยู่แล้ว ข้ามไป task ถัดไป
  ```

  After (step 2 removed; step 3 becomes step 2, test-pyramid Skill removed):
  ```markdown
  2. **เขียน test ที่ล้มเหลวก่อน (RED)**
     เลือก test level จาก inline guidance ด้านบน (unit / integration / e2e)
     แล้วเขียน test ที่ capture behavior ที่ต้องการ
     — test ต้อง fail ก่อนเสมอ รัน `make test-unit` เพื่อยืนยัน
     ถ้า test ผ่านแล้ว → feature มีอยู่แล้ว ข้ามไป task ถัดไป
     If the plan frontmatter has `tdd: deep` → invoke `Skill(zie-framework:tdd-loop)` for this task instead.
  ```

  Renumber subsequent steps (old 4→3, old 5→4, etc.) to keep sequence correct.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full `## Steps` section and confirm:
  - Step numbering is consecutive (1, 2, 3, 4, 5, 6, 7, 8 — no gaps)
  - `Skill(zie-framework:verify)` in the post-loop section is untouched
  - `Skill(zie-framework:debug)` in the `## เมื่อ test ล้มเหลว` section is untouched — the failure path calls `debug`, not `tdd-loop`; this is correct and must not be changed
  - The inline guidance block reads cleanly as printed output (no nested code fences breaking render)

  Run: `make test-unit` — still PASS

---

## Task 2: Parallel-by-default task execution

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/zie-implement.md` `### วิเคราะห์ dependency ระหว่าง tasks` section describes tasks without `depends_on` as running in parallel by default
- Tasks with `<!-- depends_on: TN -->` annotation still run sequentially after their dependency
- The logic is expressed as: no annotation = parallel; annotation present = sequential after dependency

**Files:**
- Modify: `commands/zie-implement.md`
- Modify: `tests/unit/test_implement_guidance_inline.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_implement_guidance_inline.py`:

  ```python
  class TestParallelByDefault:
      def test_parallel_by_default_logic_present(self):
          text = read_cmd()
          # The dependency section must express that no depends_on = parallel
          assert "no depends_on" in text or "without depends_on" in text or \
                 "no `depends_on`" in text, \
              "Parallel-by-default logic must state tasks without depends_on run in parallel"

      def test_depends_on_sequential_logic_present(self):
          text = read_cmd()
          assert "depends_on" in text, \
              "Sequential depends_on annotation logic must still be present"
  ```

  Run: `make test-unit` — must FAIL (current wording says "Group tasks with no depends_on → independent" but does not explicitly state the parallel-by-default inversion)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, replace the `### วิเคราะห์ dependency ระหว่าง tasks` section body:

  Before:
  ```markdown
  Before starting tasks:

  - Parse all tasks in plan for `<!-- depends_on: T1, T2 -->` comments
  - Group tasks with no depends_on → **independent** (can run in parallel)
  - Tasks with depends_on → **dependent** (run after blocking tasks complete)
  - Spawn min(independent_count, 4) parallel agents for independent tasks
  - If 0 independent tasks → execute all sequentially in dependency order
  ```

  After:
  ```markdown
  Before starting tasks:

  **Default: parallel.** Tasks with no `depends_on` annotation run in parallel.
  Tasks annotated with `<!-- depends_on: T1, T2 -->` run sequentially after all
  listed dependencies complete.

  - Parse all tasks in plan for `<!-- depends_on: TN -->` comments
  - Tasks without `depends_on` → **parallel** (default path) — spawn up to 4 concurrent agents
  - Tasks with `depends_on` → **sequential** — start only after each listed task ID is complete
  - If all tasks have `depends_on` chains → execute in full dependency order (no parallelism)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm the dependency section is still under the same heading and that the
  surrounding `## ตรวจสอบก่อนเริ่ม` and `## Steps` sections are untouched.
  Confirm wording is unambiguous: plan authors who want sequential-only must
  add `depends_on` to every task after the first.

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-implement.md tests/unit/test_implement_guidance_inline.py && git commit -m "feat: implement-guidance-inline"`*
