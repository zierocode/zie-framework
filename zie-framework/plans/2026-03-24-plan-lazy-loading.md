---
approved: false
approved_at: ~
backlog: backlog/plan-lazy-loading.md
spec: specs/2026-03-24-plan-lazy-loading-design.md
---

# Plan Lazy Loading — Implementation Plan

**Goal:** Change `/zie-implement` from reading the entire plan file at startup to a two-stage read: header-only at startup, then per-task section read immediately before each task executes. Reduces context footprint by 60–80% for multi-task plans.

**Architecture:** Single file modification — `commands/zie-implement.md`. Replace the current "Read plan file → check frontmatter" instruction in the startup checklist with a header-only read instruction. Add a per-task read instruction at the start of the task loop. No changes to plan file format, no changes to `/zie-plan` approval flow.

**Tech Stack:** Markdown (command definition), pytest + pathlib (tests)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Replace full-plan read at startup with header-only read; add per-task section read before each task |
| Create | `tests/unit/test_plan_lazy_loading.py` | Verify header-only instruction present, per-task instruction present, full-plan read instruction absent |

---

## Task 1: Update `commands/zie-implement.md` for lazy loading

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-implement.md` contains the instruction: `Read plan header only: everything up to (not including) the first \`### Task\` heading`
- `commands/zie-implement.md` contains the instruction: `Read this task's full section from the plan file (from its \`### Task N\` heading to the next \`### Task\` heading or EOF)`
- `commands/zie-implement.md` does NOT contain: `Read plan file → check frontmatter for \`approved: true\``
- All other startup checks and task loop logic are unchanged

**Files:**
- Modify: `commands/zie-implement.md`
- Create: `tests/unit/test_plan_lazy_loading.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_plan_lazy_loading.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  class TestPlanLazyLoading:
      def test_header_only_read_instruction_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert (
              "Read plan header only: everything up to (not including) the first `### Task` heading"
              in text
          ), "zie-implement.md must contain the header-only read instruction"

      def test_per_task_section_read_instruction_present(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert (
              "Read this task's full section from the plan file (from its `### Task N` heading to the next `### Task` heading or EOF)"
              in text
          ), "zie-implement.md must contain the per-task section read instruction"

      def test_full_plan_read_at_startup_absent(self):
          text = (COMMANDS_DIR / "zie-implement.md").read_text()
          assert (
              "Read plan file → check frontmatter for `approved: true`" not in text
          ), "zie-implement.md must NOT contain the full-plan read at startup instruction"
  ```

  Run: `make test-unit` — must FAIL (instructions not yet present / old instruction still present)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-implement.md`, step 3 of "ตรวจสอบก่อนเริ่ม" currently reads:

  ```
     - Read plan file → check frontmatter for `approved: true`.
  ```

  Replace that single line with:

  ```
     - Read plan header only: everything up to (not including) the first `### Task` heading
       — check frontmatter for `approved: true`.
  ```

  Then in `## Steps` → `### วนรอบ task จนครบ`, insert a new sub-step immediately before the existing step 1 ("Announce task"):

  ```
  0. **Read task section**: Read this task's full section from the plan file (from its `### Task N` heading to the next `### Task` heading or EOF). This is the only time this task's detail enters context.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read `commands/zie-implement.md` in full. Confirm:
  - Startup checklist step numbering is intact (steps 1–8 flow correctly)
  - Task loop step numbering is intact (renumber if step 0 is awkward — move read-task-section into step 1 preamble instead)
  - No duplicate read instructions
  - `/zie-plan` approval section is untouched

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-implement.md tests/unit/test_plan_lazy_loading.py && git commit -m "feat: plan-lazy-loading"`*
