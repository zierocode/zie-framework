---
approved: false
approved_at: ~
backlog: backlog/skill-content-pruning.md
spec: specs/2026-03-24-skill-content-pruning-design.md
---

# Skill Content Pruning — Implementation Plan

**Goal:** Remove tutorial prose, illustrative examples, and explanatory scaffolding from all 10 skill files to reduce per-invocation token cost by ≥30% in at least 5 skills without changing any skill's behavior.
**Architecture:** Pure content edits to existing Markdown files — no new files, no structural changes. Tests verify specific verbose strings are absent and core behavior strings are present after each edit.
**Tech Stack:** Markdown (skill files), pytest (content tests)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/tdd-loop/SKILL.md` | Remove Cycle Time Target section |
| Modify | `skills/test-pyramid/SKILL.md` | Remove BAD/GOOD examples, Playwright code block, config essentials |
| Modify | `skills/write-plan/SKILL.md` | Remove future-skill-authors note, Context from brain stub |
| Modify | `skills/spec-design/SKILL.md` | Remove future-skill-authors note |
| Modify | `skills/spec-reviewer/SKILL.md` | No removable content — verified clean |
| Modify | `skills/plan-reviewer/SKILL.md` | No removable content — verified clean |
| Modify | `skills/impl-reviewer/SKILL.md` | No removable content — verified clean |
| Modify | `skills/debug/SKILL.md` | Remove illustrative bash example block in Reproduce step |
| Modify | `skills/verify/SKILL.md` | Remove explanatory preamble sentence |
| Modify | `skills/retro-format/SKILL.md` | Remove all five worked-example code blocks |
| Create | `tests/unit/test_skill_pruning.py` | Verify absent verbose strings + present behavior strings |

---

## Task 1: Prune `skills/tdd-loop/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Lines 57-60 (`## Cycle Time Target` section, 4 lines) are absent from the file
- Core rule strings (`Never skip RED`, `One failing test at a time`) remain present
- Test Quality Checklist (lines 62-68) is preserved intact
- Line count decreases by at least 4 lines

**Files:**
- Modify: `skills/tdd-loop/SKILL.md`
- Create: `tests/unit/test_skill_pruning.py`

**Lines to remove** (exact content from current file):

```
## Cycle Time Target

Each RED→GREEN→REFACTOR cycle should take < 15 minutes.
If stuck > 15 minutes on GREEN → stop, invoke systematic-debugging skill.
```

That is lines 57–60 inclusive (the blank line before the next section header stays).

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py
  from pathlib import Path

  SKILLS_DIR = Path(__file__).parents[2] / "skills"


  def read_skill(skill: str) -> str:
      return (SKILLS_DIR / skill / "SKILL.md").read_text()


  class TestTddLoopPruning:
      def test_cycle_time_target_section_absent(self):
          text = read_skill("tdd-loop")
          assert "## Cycle Time Target" not in text, \
              "Cycle Time Target section must be removed"

      def test_cycle_time_prose_absent(self):
          text = read_skill("tdd-loop")
          assert "Each RED→GREEN→REFACTOR cycle should take < 15 minutes." not in text, \
              "Cycle time prose must be removed"

      def test_stuck_15_minutes_line_absent(self):
          text = read_skill("tdd-loop")
          assert "If stuck > 15 minutes on GREEN" not in text, \
              "Stuck-15-minutes line must be removed"

      def test_core_rules_preserved(self):
          text = read_skill("tdd-loop")
          assert "Never skip RED" in text
          assert "One failing test at a time" in text

      def test_quality_checklist_preserved(self):
          text = read_skill("tdd-loop")
          assert "## Test Quality Checklist" in text
          assert "Test name describes expected behavior" in text
  ```

  Run: `make test-unit` — must FAIL (`## Cycle Time Target` still present)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/tdd-loop/SKILL.md`: delete lines 57–60 (the `## Cycle Time Target` header and its two body lines plus the trailing blank line between the rules section and checklist).

  Exact removal — delete these 4 lines:
  ```
  ## Cycle Time Target

  Each RED→GREEN→REFACTOR cycle should take < 15 minutes.
  If stuck > 15 minutes on GREEN → stop, invoke systematic-debugging skill.
  ```

  The blank line separating `## กฎที่ต้องทำตาม` from `## Test Quality Checklist` is preserved.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the edited file. Confirm no orphaned blank lines created. Confirm `## กฎที่ต้องทำตาม` block and `## Test Quality Checklist` block are still intact and correctly separated.

  Run: `make test-unit` — still PASS

---

## Task 2: Prune `skills/test-pyramid/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- The `## เขียน Test ที่ดี` section (lines 85–101, 17 lines) is absent
- The Playwright code block (lines 103–117, 15 lines) is absent
- The `## Playwright Specifics` header and `playwright.config.ts` essentials bullets (lines 103–126, 24 lines) are absent
- The pyramid ASCII art, project-type tables, and trigger table remain intact
- Line count decreases by at least 40 lines

**Files:**
- Modify: `skills/test-pyramid/SKILL.md`
- Modify: `tests/unit/test_skill_pruning.py`

**Lines to remove** — two contiguous blocks:

Block A (lines 85–101): entire `## เขียน Test ที่ดี` section including the BAD/GOOD name examples and "Integration tests must use real external services" note:
```
## เขียน Test ที่ดี

**Name tests as behavior, not implementation:**

- BAD: `test_hybrid_search_function`
- GOOD: `test_should_return_most_relevant_memory_first`

**Focus E2E on user journeys, not page coverage:**

- BAD: "test every page loads"
- GOOD: "test user can save a memory and find it by search"

**Integration tests must use real external services:**

- Real PostgreSQL (not SQLite)
- Real HTTP calls via TestClient (not mocked)
- If it can't run without infrastructure, mark it `@pytest.mark.integration`
```

Block B (lines 103–126): entire `## Playwright Specifics` section including typescript code block and config bullets:
```
## Playwright Specifics

```typescript
// tests/e2e/fixtures.ts — shared setup
import { test as base } from '@playwright/test';
export const test = base.extend({ /* project fixtures */ });

// Focus on user journeys
test('user can search memories', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="search-input"]', 'vue framework');
  await page.keyboard.press('Enter');
  await expect(page.locator('[data-testid="result"]')).toBeVisible();
});
```

**`playwright.config.ts` essentials:**

- `baseURL` from env (works locally + CI)
- `retries: 1` in CI (catch flaky tests, not hide them)
- `screenshot: 'only-on-failure'`
- `video: 'retain-on-failure'`
- Run on chromium only for speed (add more for pre-release only)
```

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestTddLoopPruning

  class TestTestPyramidPruning:
      def test_bad_good_name_examples_absent(self):
          text = read_skill("test-pyramid")
          assert "BAD: `test_hybrid_search_function`" not in text, \
              "BAD/GOOD name examples must be removed"

      def test_bad_good_e2e_examples_absent(self):
          text = read_skill("test-pyramid")
          assert 'BAD: "test every page loads"' not in text, \
              "BAD/GOOD E2E examples must be removed"

      def test_playwright_code_block_absent(self):
          text = read_skill("test-pyramid")
          assert "tests/e2e/fixtures.ts" not in text, \
              "Playwright fixtures.ts example must be removed"

      def test_playwright_config_essentials_absent(self):
          text = read_skill("test-pyramid")
          assert "playwright.config.ts" not in text, \
              "playwright.config.ts essentials section must be removed"

      def test_retries_config_example_absent(self):
          text = read_skill("test-pyramid")
          assert "`retries: 1` in CI" not in text, \
              "retries config example must be removed"

      def test_pyramid_ascii_preserved(self):
          text = read_skill("test-pyramid")
          assert "UNIT TESTS" in text
          assert "Playwright" in text

      def test_trigger_table_preserved(self):
          text = read_skill("test-pyramid")
          assert "PostToolUse hook" in text
          assert "/zie-release gate" in text
  ```

  Run: `make test-unit` — must FAIL (both sections still present)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/test-pyramid/SKILL.md`:
  1. Delete the blank line before `## เขียน Test ที่ดี` plus the entire section through the `@pytest.mark.integration` bullet (lines 84–101 inclusive, 18 lines).
  2. Delete the blank line before `## Playwright Specifics` plus the entire section to end of file (lines 102–126 inclusive, 25 lines).

  File ends after the trigger table (`| Debugging a failing test | Relevant unit only |`).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the edited file end-to-end. Confirm file ends cleanly after the trigger table with no trailing blank lines beyond one. Confirm pyramid, project-type sections, and trigger table are all intact.

  Run: `make test-unit` — still PASS

---

## Task 3: Prune `skills/write-plan/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- The `> **Note for future skill authors:**` callout block (lines 30–33, 4 lines) is absent
- The `## Context from brain` section (lines 105–109, 5 lines) is absent
- All format specs, task structure template, and save/reviewer-loop instructions remain intact
- Line count decreases by at least 9 lines

**Files:**
- Modify: `skills/write-plan/SKILL.md`
- Modify: `tests/unit/test_skill_pruning.py`

**Lines to remove:**

Block A (lines 30–33): future-skill-authors callout:
```
> **Note for future skill authors:** if this skill bundles helper scripts,
> reference them via `${CLAUDE_SKILL_DIR}/scripts/<script-name>` — Claude Code
> resolves this to the skill's own directory regardless of CWD.
```
(plus the blank line following it at line 34)

Block B (lines 105–109): Context from brain section:
```
## Context from brain

_Prior memories relevant to this feature are surfaced here by /zie-plan before
handing off to /zie-implement._
```
(plus the blank line preceding it at line 104)

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestTestPyramidPruning

  class TestWritePlanPruning:
      def test_future_skill_authors_note_absent(self):
          text = read_skill("write-plan")
          assert "Note for future skill authors" not in text, \
              "Future skill authors note must be removed"

      def test_claude_skill_dir_reference_absent(self):
          text = read_skill("write-plan")
          assert "CLAUDE_SKILL_DIR" not in text, \
              "CLAUDE_SKILL_DIR reference must be removed"

      def test_context_from_brain_section_absent(self):
          text = read_skill("write-plan")
          assert "## Context from brain" not in text, \
              "Context from brain section must be removed"

      def test_prior_memories_prose_absent(self):
          text = read_skill("write-plan")
          assert "_Prior memories relevant to this feature are surfaced here" not in text, \
              "Prior memories stub prose must be removed"

      def test_plan_header_format_preserved(self):
          text = read_skill("write-plan")
          assert "approved: false" in text
          assert "## โครงสร้าง Task" in text

      def test_reviewer_loop_preserved(self):
          text = read_skill("write-plan")
          assert "plan-reviewer" in text
          assert "Max 3 iterations" in text
  ```

  Run: `make test-unit` — must FAIL (both blocks still present)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/write-plan/SKILL.md`:
  1. Delete lines 30–34 (the blockquote callout plus its following blank line).
  2. Delete lines 104–109 (the blank line before the section header, the `## Context from brain` header, and its two body lines plus trailing blank line).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the edited file. Confirm the `## เตรียม context` section flows directly into `## Plan Document Header`. Confirm `## บันทึกไว้ที่` section flows directly into `## Notes`. No orphaned blank lines.

  Run: `make test-unit` — still PASS

---

## Task 4: Prune `skills/spec-design/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- The `> **Note for future skill authors:**` callout block (lines 30–33, 4 lines) is absent
- All Steps 1–9, format specs, and reviewer loop instructions remain intact
- Line count decreases by at least 4 lines

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Modify: `tests/unit/test_skill_pruning.py`

**Lines to remove** (lines 30–33 plus blank line at 34):

```
> **Note for future skill authors:** if this skill bundles helper scripts,
> reference them via `${CLAUDE_SKILL_DIR}/scripts/<script-name>` — Claude Code
> resolves this to the skill's own directory regardless of CWD.
```

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestWritePlanPruning

  class TestSpecDesignPruning:
      def test_future_skill_authors_note_absent(self):
          text = read_skill("spec-design")
          assert "Note for future skill authors" not in text, \
              "Future skill authors note must be removed"

      def test_claude_skill_dir_reference_absent(self):
          text = read_skill("spec-design")
          assert "CLAUDE_SKILL_DIR" not in text, \
              "CLAUDE_SKILL_DIR reference must be removed"

      def test_steps_preserved(self):
          text = read_skill("spec-design")
          assert "Understand the idea" in text
          assert "Spec reviewer loop" in text
          assert "Record approval" in text

      def test_spec_format_preserved(self):
          text = read_skill("spec-design")
          assert "**Problem:**" in text
          assert "**Out of Scope:**" in text
  ```

  Run: `make test-unit` — must FAIL (`CLAUDE_SKILL_DIR` still present)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/spec-design/SKILL.md`: delete lines 30–34 (the blockquote callout and its following blank line).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the file. Confirm `## เตรียม context` flows directly into `## Steps` with no extra blank lines.

  Run: `make test-unit` — still PASS

---

## Task 5: Audit `skills/spec-reviewer/SKILL.md` — no pruning required

<!-- depends_on: none -->

**Acceptance Criteria:**
- File confirmed to contain no illustrative examples, BAD/GOOD blocks, or tutorial prose
- A no-op test asserts that all behavioral sections are present (Phase 1, Phase 2, Phase 3, Output Format, Notes)
- File is NOT modified

**Files:**
- Modify: `tests/unit/test_skill_pruning.py`

**Rationale:** `spec-reviewer/SKILL.md` (95 lines) contains only the review checklist, phase structure, output format, and minimal notes. No worked examples, no BAD/GOOD patterns, no tutorial prose. Zero removable content.

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestSpecDesignPruning

  class TestSpecReviewerAudit:
      def test_phase_1_present(self):
          text = read_skill("spec-reviewer")
          assert "## Phase 1" in text

      def test_phase_2_present(self):
          text = read_skill("spec-reviewer")
          assert "## Phase 2" in text

      def test_phase_3_present(self):
          text = read_skill("spec-reviewer")
          assert "## Phase 3" in text

      def test_output_format_present(self):
          text = read_skill("spec-reviewer")
          assert "## Output Format" in text

      def test_approved_verdict_present(self):
          text = read_skill("spec-reviewer")
          assert "APPROVED" in text

      def test_no_bad_good_examples(self):
          text = read_skill("spec-reviewer")
          assert "BAD:" not in text
          assert "GOOD:" not in text
  ```

  Run: `make test-unit` — must PASS immediately (file unchanged, tests are assertions of existing state)

- [ ] **Step 2: Implement (GREEN)**

  No file edits. Tests already pass.

- [ ] **Step 3: Refactor**

  No changes. Confirm test class exists and passes.

  Run: `make test-unit` — still PASS

---

## Task 6: Audit `skills/plan-reviewer/SKILL.md` — no pruning required

<!-- depends_on: none -->

**Acceptance Criteria:**
- File confirmed clean (no illustrative examples or tutorial prose)
- No-op tests assert all behavioral sections present
- File is NOT modified

**Files:**
- Modify: `tests/unit/test_skill_pruning.py`

**Rationale:** `plan-reviewer/SKILL.md` (99 lines) mirrors spec-reviewer in structure. All content is behavioral checklist items. The "Pattern match" Phase 3 item is a required decision rule, not an example.

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestSpecReviewerAudit

  class TestPlanReviewerAudit:
      def test_phase_1_present(self):
          text = read_skill("plan-reviewer")
          assert "## Phase 1" in text

      def test_phase_2_present(self):
          text = read_skill("plan-reviewer")
          assert "## Phase 2" in text

      def test_phase_3_present(self):
          text = read_skill("plan-reviewer")
          assert "## Phase 3" in text

      def test_output_format_present(self):
          text = read_skill("plan-reviewer")
          assert "## Output Format" in text

      def test_tdd_structure_check_present(self):
          text = read_skill("plan-reviewer")
          assert "TDD structure" in text

      def test_no_bad_good_examples(self):
          text = read_skill("plan-reviewer")
          assert "BAD:" not in text
          assert "GOOD:" not in text
  ```

  Run: `make test-unit` — must PASS immediately

- [ ] **Step 2: Implement (GREEN)**

  No file edits.

- [ ] **Step 3: Refactor**

  No changes. Confirm test class passes.

  Run: `make test-unit` — still PASS

---

## Task 7: Audit `skills/impl-reviewer/SKILL.md` — no pruning required

<!-- depends_on: none -->

**Acceptance Criteria:**
- File confirmed clean
- No-op tests assert all behavioral sections present
- File is NOT modified

**Files:**
- Modify: `tests/unit/test_skill_pruning.py`

**Rationale:** `impl-reviewer/SKILL.md` (91 lines) is all checklist. No examples, no worked prose.

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestPlanReviewerAudit

  class TestImplReviewerAudit:
      def test_phase_1_present(self):
          text = read_skill("impl-reviewer")
          assert "## Phase 1" in text

      def test_phase_2_present(self):
          text = read_skill("impl-reviewer")
          assert "## Phase 2" in text

      def test_phase_3_present(self):
          text = read_skill("impl-reviewer")
          assert "## Phase 3" in text

      def test_output_format_present(self):
          text = read_skill("impl-reviewer")
          assert "## Output Format" in text

      def test_ac_coverage_check_present(self):
          text = read_skill("impl-reviewer")
          assert "AC coverage" in text

      def test_no_bad_good_examples(self):
          text = read_skill("impl-reviewer")
          assert "BAD:" not in text
          assert "GOOD:" not in text
  ```

  Run: `make test-unit` — must PASS immediately

- [ ] **Step 2: Implement (GREEN)**

  No file edits.

- [ ] **Step 3: Refactor**

  No changes.

  Run: `make test-unit` — still PASS

---

## Task 8: Prune `skills/debug/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- The illustrative bash command block inside the Reproduce step (lines 30–33, 4 lines) is absent
- The four-phase structure (Reproduce, Isolate, Fix, Verify) remains intact
- The memory recall/remember calls remain intact
- The rules section remains intact
- Line count decreases by at least 4 lines

**Files:**
- Modify: `skills/debug/SKILL.md`
- Modify: `tests/unit/test_skill_pruning.py`

**Lines to remove** (lines 30–33): the illustrative bash command inside "ทำซ้ำ bug":

```
3. Run the failing test in isolation:

   ```bash
   python3 -m pytest tests/path/test_file.py::TestClass::test_method -v
   ```
```

This is a 4-line illustrative example. The actionable instruction is step 3's header line: "Run the failing test in isolation" — the example path is not a required command. The actual run commands are defined per-project in each plan.

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestImplReviewerAudit

  class TestDebugPruning:
      def test_illustrative_pytest_path_absent(self):
          text = read_skill("debug")
          assert "tests/path/test_file.py::TestClass::test_method" not in text, \
              "Illustrative pytest path example must be removed"

      def test_reproduce_step_preserved(self):
          text = read_skill("debug")
          assert "ทำซ้ำ bug" in text
          assert "Run the failing test in isolation" in text

      def test_isolate_step_preserved(self):
          text = read_skill("debug")
          assert "แยกปัญหา" in text
          assert "Form a hypothesis" in text

      def test_fix_step_preserved(self):
          text = read_skill("debug")
          assert "แก้ bug" in text

      def test_verify_step_preserved(self):
          text = read_skill("debug")
          assert "ตรวจยืนยัน" in text
          assert "make test-unit" in text

      def test_rules_preserved(self):
          text = read_skill("debug")
          assert "Never comment out a failing test" in text
          assert "Never skip the reproduction step" in text
  ```

  Run: `make test-unit` — must FAIL (`tests/path/test_file.py::TestClass::test_method` still present)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/debug/SKILL.md`: in the `### ทำซ้ำ bug (Reproduce)` section, delete step 3's sub-block — the line `3. Run the failing test in isolation:` is kept but the fenced bash block below it (4 lines including the blank line before it) is removed.

  Exact lines to delete:
  ```

     ```bash
     python3 -m pytest tests/path/test_file.py::TestClass::test_method -v
     ```
  ```

  Step 3 becomes: `3. Run the failing test in isolation.` (the blank line and code block that followed it are removed).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the edited file. Confirm step numbering in Reproduce phase is still 1–4 with no gaps. Confirm the fenced block is fully gone with no orphaned backticks.

  Run: `make test-unit` — still PASS

---

## Task 9: Prune `skills/verify/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Line 13 (`Catch problems before they reach main.`) is absent
- Line 14 (blank) is collapsed so the header flows directly into the checklist
- All five checklist sections (Tests, regressions, TODOs, code review, Documentation) remain intact
- Summary block format preserved
- Line count decreases by at least 2 lines

**Files:**
- Modify: `skills/verify/SKILL.md`
- Modify: `tests/unit/test_skill_pruning.py`

**Lines to remove** (lines 13–14):

```
Catch problems before they reach main.

```

The skill header already sets context (`# verify — Pre-Ship Verification`). The sentence is pure preamble.

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestDebugPruning

  class TestVerifyPruning:
      def test_preamble_sentence_absent(self):
          text = read_skill("verify")
          assert "Catch problems before they reach main." not in text, \
              "Preamble sentence must be removed"

      def test_test_section_preserved(self):
          text = read_skill("verify")
          assert "make test-unit" in text
          assert "make test-int" in text

      def test_todo_grep_preserved(self):
          text = read_skill("verify")
          assert "TODO\\|FIXME\\|PLACEHOLDER" in text

      def test_summary_block_preserved(self):
          text = read_skill("verify")
          assert "Verification complete:" in text
          assert "Ready to ship" in text

      def test_documentation_section_preserved(self):
          text = read_skill("verify")
          assert "CLAUDE.md" in text
          assert "README.md" in text
  ```

  Run: `make test-unit` — must FAIL (`Catch problems before they reach main.` still present)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/verify/SKILL.md`: delete line 13 (`Catch problems before they reach main.`) and the blank line 14 that follows it.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the file. Confirm `# verify — Pre-Ship Verification` header is immediately followed by `## รายการตรวจสอบ` with a single blank line between them.

  Run: `make test-unit` — still PASS

---

## Task 10: Prune `skills/retro-format/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- All five worked-example `text` code blocks (one per retro section) are absent
- Section headers and their instructional prose remain intact
- ADR template, ADR criteria, frequency table, and ROADMAP checklist remain intact
- Line count decreases by at least 40 lines (5 blocks × ~8–10 lines each)

**Files:**
- Modify: `skills/retro-format/SKILL.md`
- Modify: `tests/unit/test_skill_pruning.py`

**Blocks to remove** — five fenced ` ```text ``` ` example blocks, one per retro section:

Block 1 — inside `### สิ่งที่ Ship ออกไป` (lines 22–26):
```
```text
- csv-export feature (v1.0.11) — memories now exportable as CSV, MD, JSON
- fix: hybrid search RRF scoring edge case with empty tags
```
```

Block 2 — inside `### สิ่งที่ทำงานได้ดี` (lines 32–37):
```
```text
- TDD cycle kept feature scope tight — no scope creep
- auto-test hook caught a regression in search.py within seconds
- zie-memory recalled the RRF pattern from a previous project
```
```

Block 3 — inside `### สิ่งที่เจ็บปวด (Pain Points)` (lines 43–47):
```
```text
- SQLAlchemy async session management with LLM calls = complex (3-phase pattern)
- Playwright setup took longer than expected — browser install in CI
```
```

Block 4 — inside `### การตัดสินใจสำคัญ` (lines 54–58):
```
```text
- Used HNSW LATERAL join for dedup instead of cross-join → O(n log n) vs O(n²)
- Split LLM calls from DB sessions → never hold connection during async LLM
```
```

Block 5 — inside `### Pattern ที่ควรจำ` (lines 63–68):
```
```text
- asyncpg CAST syntax: always CAST(:param AS vector), never :param::vector
- Pre-flight dedup in every write path prevents duplicates without extra API
  calls
```
```

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_pruning.py — add after TestVerifyPruning

  class TestRetroFormatPruning:
      def test_csv_export_example_absent(self):
          text = read_skill("retro-format")
          assert "csv-export feature (v1.0.11)" not in text, \
              "Ship example block must be removed"

      def test_tdd_scope_tight_example_absent(self):
          text = read_skill("retro-format")
          assert "TDD cycle kept feature scope tight" not in text, \
              "Worked-well example block must be removed"

      def test_sqlalchemy_example_absent(self):
          text = read_skill("retro-format")
          assert "SQLAlchemy async session management with LLM calls" not in text, \
              "Pain points example block must be removed"

      def test_hnsw_example_absent(self):
          text = read_skill("retro-format")
          assert "HNSW LATERAL join for dedup" not in text, \
              "Decisions example block must be removed"

      def test_asyncpg_cast_example_absent(self):
          text = read_skill("retro-format")
          assert "asyncpg CAST syntax" not in text, \
              "Patterns example block must be removed"

      def test_section_headers_preserved(self):
          text = read_skill("retro-format")
          assert "### สิ่งที่ Ship ออกไป" in text
          assert "### สิ่งที่ทำงานได้ดี" in text
          assert "### สิ่งที่เจ็บปวด" in text
          assert "### การตัดสินใจสำคัญ" in text
          assert "### Pattern ที่ควรจำ" in text

      def test_adr_template_preserved(self):
          text = read_skill("retro-format")
          assert "## รูปแบบ ADR" in text
          assert "## Context" in text
          assert "## Decision" in text
          assert "## Consequences" in text

      def test_frequency_table_preserved(self):
          text = read_skill("retro-format")
          assert "## ความถี่ของ Retro" in text
          assert "After /zie-release" in text

      def test_roadmap_checklist_preserved(self):
          text = read_skill("retro-format")
          assert "## Checklist อัปเดต ROADMAP" in text
          assert "All shipped items moved to Done" in text
  ```

  Run: `make test-unit` — must FAIL (all five example blocks still present)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/retro-format/SKILL.md`: remove all five fenced ` ```text ``` ` example blocks (and their immediately preceding blank lines). The instructional prose line above each block (e.g. `List every feature, fix, or improvement that was completed. Include version if released.`) is kept.

  After removal each section reads: header → one or two instructional sentences → no code block → next section.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full edited file. Confirm:
  - Five section headers all present under `## โครงสร้าง Retrospective`
  - ADR template block (the `# ADR-NNN` markdown block) is NOT removed — it is a required format spec, not a worked example
  - `**What does NOT need an ADR:**` list is intact
  - Frequency table intact
  - ROADMAP checklist intact

  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/*/SKILL.md tests/unit/test_skill_pruning.py && git commit -m "feat: skill-content-pruning — remove tutorial prose from all 10 skills"`*
