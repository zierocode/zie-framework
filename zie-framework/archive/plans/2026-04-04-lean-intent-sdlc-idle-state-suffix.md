---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-intent-sdlc-idle-state-suffix.md
---

# Lean Intent SDLC Idle State Suffix — Implementation Plan

**Goal:** Suppress the SDLC state suffix in `intent-sdlc.py` when the project is idle and intent is unambiguous (score ≥ 2), eliminating ~60 chars of zero-information overhead from the most common state.

**Architecture:** A single boolean flag `suppress_suffix` is evaluated immediately before the suffix `parts.append(...)` call in `intent-sdlc.py`. The condition uses an explicit `best is not None` guard followed by `scores.get(best, 0) >= 2`, then only proceeds with suppression when `stage == "idle"` and `active_task == "none"`. No new functions, no structural changes — one conditional wraps the existing append.

**Tech Stack:** Python 3.x, pytest, subprocess-based hook test harness.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/intent-sdlc.py` | Add `suppress_suffix` condition before suffix append (lines 324–326) |
| Modify | `tests/unit/test_intent_sdlc_early_exit.py` | Add `TestIdleStateSuffixSuppression` class with 5 cases |

---

## Task Sizing Check

Two tasks, each touching one file. No file conflicts. S plan (≤ 3 tasks). Tasks are independent: tests can be written first, then implementation makes them pass.

---

## Task 1: Add suffix suppression to `hooks/intent-sdlc.py`

**Acceptance Criteria:**
- When `stage == "idle"`, `active_task == "none"`, `best is not None`, and `scores[best] >= 2`: the suffix `task:... | stage:... | next:... | tests:...` is absent from hook output.
- When any condition is false (active task, score < 2, best is None, non-idle stage): the suffix is present as before.
- Gate messages and no-track messages are unaffected.
- All existing tests pass.

**Files:**
- Modify: `hooks/intent-sdlc.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add `TestIdleStateSuffixSuppression` to `tests/unit/test_intent_sdlc_early_exit.py` (Task 2 below). Running those tests before this task will produce failures. To isolate just this task's RED signal, confirm existing tests pass:

  ```
  make test-unit
  ```
  Expected: all existing tests PASS (baseline).

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/intent-sdlc.py`, replace lines 324–326:

  ```python
  parts.append(
      f"task:{active_task} | stage:{stage} | next:{suggested_cmd} | tests:{test_status}"
  )
  ```

  with:

  ```python
  suppress_suffix = (
      stage == "idle"
      and active_task == "none"
      and best is not None
      and scores.get(best, 0) >= 2
  )
  if not suppress_suffix:
      parts.append(
          f"task:{active_task} | stage:{stage} | next:{suggested_cmd} | tests:{test_status}"
      )
  ```

  Run: `make test-unit` — existing tests must PASS. New suffix-suppression tests (Task 2) must also PASS after Task 2 is done.

- [ ] **Step 3: Refactor**

  No structural cleanup needed — the condition is already one logical block. Verify the variable name `suppress_suffix` is consistent with hook output convention (`[zie-framework] key: value` INFO convention does not apply here — this is internal logic).

  Run: `make test-unit` — still PASS.

---

## Task 2: Add `TestIdleStateSuffixSuppression` to test file

<!-- depends_on: none — write tests before or after Task 1; they go RED until Task 1 is complete -->

**Acceptance Criteria:**
- 5 test cases cover: suppress on score ≥ 2 + idle, retain on score 1 + idle, retain on active task + high score, retain when best is None (unreachable in practice but guarded), retain on non-idle stage.
- Each test asserts suffix presence/absence by checking `"stage:idle"` in decoded output.
- All tests are in class `TestIdleStateSuffixSuppression` in `tests/unit/test_intent_sdlc_early_exit.py`.

**Files:**
- Modify: `tests/unit/test_intent_sdlc_early_exit.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append the following class to `tests/unit/test_intent_sdlc_early_exit.py`:

  ```python
  class TestIdleStateSuffixSuppression:
      """Suffix is suppressed when idle + active_task==none + best is not None + score>=2."""

      def test_suppressed_when_idle_and_score_ge2(self, tmp_path):
          # "implement" + "bug" + "fix" → fix category hits multiple patterns → score ≥ 2
          # ROADMAP has empty Now section → idle state
          cwd = make_cwd_with_zf(tmp_path, roadmap_content="## Now\n\n## Next\n")
          r = run_hook(
              "there is a bug and it is broken and it failed completely",
              tmp_cwd=cwd,
              session_id="test-suppress-idle-score2",
          )
          assert r.returncode == 0
          assert r.stdout.strip() != ""
          out = json.loads(r.stdout)
          ctx = out["additionalContext"]
          assert "stage:idle" not in ctx, f"Suffix should be suppressed; got: {ctx}"

      def test_retained_when_idle_and_score_eq1(self, tmp_path):
          # Single-pattern match → score == 1 → suffix retained
          cwd = make_cwd_with_zf(tmp_path, roadmap_content="## Now\n\n## Next\n")
          r = run_hook(
              "i would like to do a release of this thing",
              tmp_cwd=cwd,
              session_id="test-retain-idle-score1",
          )
          assert r.returncode == 0
          assert r.stdout.strip() != ""
          out = json.loads(r.stdout)
          ctx = out["additionalContext"]
          assert "stage:idle" in ctx, f"Suffix should be retained; got: {ctx}"

      def test_retained_when_active_task_present(self, tmp_path):
          # Now section has an item → stage != idle → suffix retained
          roadmap = "## Now\n- implement auth feature — in progress\n\n## Next\n"
          cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
          r = run_hook(
              "there is a bug and it is broken and it failed completely",
              tmp_cwd=cwd,
              session_id="test-retain-active-task",
          )
          assert r.returncode == 0
          assert r.stdout.strip() != ""
          out = json.loads(r.stdout)
          ctx = out["additionalContext"]
          # active task is present → stage will not be idle
          assert "task:none" not in ctx, f"Should show active task; got: {ctx}"

      def test_retained_when_non_idle_stage(self, tmp_path):
          # Now section has a release item → stage == release → suffix retained
          roadmap = "## Now\n- release v2.0 — merge to main\n\n## Next\n"
          cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
          r = run_hook(
              "there is a bug and it is broken and it failed completely",
              tmp_cwd=cwd,
              session_id="test-retain-release-stage",
          )
          assert r.returncode == 0
          assert r.stdout.strip() != ""
          out = json.loads(r.stdout)
          ctx = out["additionalContext"]
          assert "stage:release" in ctx, f"Suffix should be retained; got: {ctx}"

      def test_suppressed_requires_all_conditions(self, tmp_path):
          # Verify score=2 + idle is sufficient for suppression
          # "bug" + "fix" + "broken" → fix category score ≥ 2
          cwd = make_cwd_with_zf(tmp_path, roadmap_content="## Now\n\n## Next\n")
          r = run_hook(
              "the bug is causing fix to be broken and failed",
              tmp_cwd=cwd,
              session_id="test-suppress-all-conditions",
          )
          assert r.returncode == 0
          out = json.loads(r.stdout) if r.stdout.strip() else {}
          if out:
              ctx = out.get("additionalContext", "")
              # If output produced: suffix should be suppressed
              assert "stage:idle" not in ctx, f"Suffix should be suppressed; got: {ctx}"
  ```

  Run: `make test-unit` — `TestIdleStateSuffixSuppression` tests must FAIL (hook not yet modified).

- [ ] **Step 2: Implement (GREEN)**

  Complete Task 1 (modify `hooks/intent-sdlc.py`). Then:

  Run: `make test-unit` — all tests including `TestIdleStateSuffixSuppression` must PASS.

- [ ] **Step 3: Refactor**

  Review test prompts for clarity. Ensure session IDs are unique across all test classes (no collision with existing `test-*` IDs in the file). No logic changes needed.

  Run: `make test-unit` — still PASS.

---

## Execution Order

1. Add tests (Task 2, Step 1) → confirm RED on new tests, GREEN on existing.
2. Modify hook (Task 1, Step 2) → confirm all tests GREEN.
3. Run `make lint` → confirm no lint errors.
4. Run `make test-ci` → final gate before commit.
