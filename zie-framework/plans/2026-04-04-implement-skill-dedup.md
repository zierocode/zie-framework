---
approved: false
approved_at:
backlog: backlog/implement-skill-dedup.md
---

# Implement Skill Dedup — Implementation Plan

**Goal:** Remove inline RED/GREEN/REFACTOR steps from `commands/zie-implement.md` and replace with a 3-line pointer that unconditionally invokes `Skill(zie-framework:tdd-loop)`.
**Architecture:** Single-file change to `commands/zie-implement.md` — delete inline TDD prose (lines 64–66 and the `tdd: deep` conditional on line 51), insert the canonical skill-pointer step, renumber the Task Loop steps, and update tests in `tests/unit/test_implement_guidance_inline.py` to match the new content.
**Tech Stack:** Markdown (command file), Python/pytest (test updates)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-implement.md` | Remove inline TDD prose; add skill-pointer step; renumber steps |
| Modify | `tests/unit/test_implement_guidance_inline.py` | Update 3 tests to match new content |

---

## Task 1: Update tests to assert the new content (RED phase — intentional FAIL)

**Intent:** This task puts the suite into a known-failing state. No production code changes here. The failing tests are the RED signal that Task 2 must satisfy.

**Acceptance Criteria:**
- `test_inline_tdd_guidance_present` asserts `Skill(zie-framework:tdd-loop)` appears in `zie-implement.md` (not bare RED/GREEN/REFACTOR prose in Task Loop)
- `test_tdd_deep_conditional_present` is removed (or converted to assert the `tdd: deep` conditional is gone from the Task Loop)
- `test_per_task_tdd_loop_skill_absent` is inverted: asserts `Skill(zie-framework:tdd-loop)` IS present
- `make test-unit` FAILS after this step (file not yet updated — this is intentional)

**Files:**
- Modify: `tests/unit/test_implement_guidance_inline.py`

- [ ] **Step 1 (RED): Write failing tests**

  Replace the three affected tests in `tests/unit/test_implement_guidance_inline.py`:

  ```python
  def test_inline_tdd_guidance_present(self):
      text = read_cmd()
      assert "Skill(zie-framework:tdd-loop)" in text, \
          "zie-implement.md must invoke Skill(zie-framework:tdd-loop) in the Task Loop"

  def test_tdd_deep_conditional_absent(self):
      """tdd: deep gate is removed; tdd-loop is unconditional."""
      text = read_cmd()
      assert "tdd: deep" not in text, \
          "tdd: deep conditional must be removed from zie-implement.md"

  def test_per_task_tdd_loop_skill_present(self):
      text = read_cmd()
      assert "Skill(zie-framework:tdd-loop)" in text, \
          "Skill(zie-framework:tdd-loop) must appear in zie-implement.md"
  ```

  Delete `test_tdd_deep_conditional_present` and rename `test_per_task_tdd_loop_skill_absent` → `test_per_task_tdd_loop_skill_present` with inverted assertion.

  Run: `make test-unit` — **must FAIL** (`zie-implement.md` still has inline prose and `tdd: deep`). This is the expected RED state.

- [ ] **Step 2 (GREEN): No action — tests remain failing intentionally**

  `commands/zie-implement.md` is NOT modified in this task. The suite stays RED. GREEN is delivered in Task 2 Step 2.

- [ ] **Step 3 (REFACTOR): Verify no stale test references**

  Verify no other test in the suite references the old test method names. Run: `make test-unit` — still FAIL (expected; Task 2 has not run yet).

---

## Task 2: Update `commands/zie-implement.md` — remove inline prose, add skill pointer

<!-- depends_on: Task 1 -->

**Intent:** This task delivers GREEN. Tests were broken in Task 1; updating `zie-implement.md` here makes them pass.

**Acceptance Criteria:**
- `commands/zie-implement.md` no longer contains `tdd: deep` in the Context Bundle section
- Task Loop steps 2–4 (inline RED/GREEN/REFACTOR) are replaced by a single 3-line pointer invoking `Skill(zie-framework:tdd-loop)`
- Old steps 5–8 are renumbered to 3–6
- `make test-unit` PASSES after this step

**Files:**
- Modify: `commands/zie-implement.md`

- [ ] **Step 1 (RED): Already failing from Task 1**

  No new test changes needed. The suite is still RED from Task 1 Step 1. This step is a reminder: confirm `make test-unit` is still failing before writing any production code.

- [ ] **Step 2 (GREEN): Update `commands/zie-implement.md`**

  **2a. Update line 51 (Context Bundle TDD note):**

  Replace:
  ```
  **TDD:** RED → GREEN → REFACTOR per task. `tdd: deep` in plan → invoke `Skill(zie-framework:tdd-loop)`.
  ```
  With:
  ```
  **TDD:** Every task uses RED → GREEN → REFACTOR via `Skill(zie-framework:tdd-loop)`.
  ```

  **2b. Replace Task Loop steps 2–4 with the 3-line pointer:**

  Remove:
  ```
  2. **→ RED (failing test)** — write failing test (RED). `make test-unit` must FAIL. (Test pass → feature exists, skip task.)
  3. **→ GREEN (implementation)** — minimum code to pass (GREEN). `make test-unit` must PASS.
  4. **→ REFACTOR (cleanup)** — clean up. `make test-unit` still PASS.
  ```

  Insert in place of steps 2–4:
  ```
  2. **→ TDD loop** — Invoke `Skill(zie-framework:tdd-loop)`. Follow it exactly.
     If tests already pass before writing any test → feature exists, skip task.
     Skill exits after REFACTOR; continue to step 3.
  ```

  **2c. Renumber old steps 5–8 → new steps 3–6:**

  - Old `5. **Risk Classification**` → `3. **Risk Classification**`
  - Old `6. **Spawn async impl-reviewer**` → `4. **Spawn async impl-reviewer**`
  - Old `7. **→ LOW risk:**` → `5. **→ LOW risk:**`
  - Old `8. TaskUpdate` → `6. TaskUpdate`

  Run: `make test-unit` — must PASS

- [ ] **Step 3 (REFACTOR): Verify and confirm**
  Run `make test-ci` (full suite). Verify file is shortened: `wc -l commands/zie-implement.md` should show a net reduction vs. pre-change (3 inline steps replaced by 1 pointer = net −2 step lines, plus 1 line from Context Bundle). Confirm `grep "tdd: deep" commands/zie-implement.md` returns empty. Tests must still PASS.
