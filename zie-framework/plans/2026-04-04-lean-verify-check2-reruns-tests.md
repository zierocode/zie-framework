---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-verify-check2-reruns-tests.md
---

# Lean Verify — Check 2 Skips Redundant test-unit Run — Implementation Plan

**Goal:** Add a `test_output` guard to check 2 in `skills/verify/SKILL.md` so
that when `test_output` is already available, the regression check reuses it
instead of triggering a second `make test-unit` run.

**Architecture:** This is a pure wording change in a single Markdown skill file.
Check 2 gains the same conditional branch that check 1 already has: if
`test_output` is provided and non-empty, parse and compare pass counts from the
existing output; otherwise fall back to running `make test-unit`. No hook or
Python code is touched.

**Tech Stack:** Markdown (skill file), pytest (tests)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/verify/SKILL.md` | Add `test_output` guard to check 2 section |
| Modify | `tests/unit/test_verify_scoped_mode.py` | Add regression test asserting check 2 guard is present |

---

## Task 1: Add `test_output` guard to check 2 in `skills/verify/SKILL.md`

**Acceptance Criteria:**
- Check 2 in `skills/verify/SKILL.md` explicitly states: if `test_output` is
  provided and non-empty, reuse it for the regression check and do not run
  `make test-unit` again.
- If `test_output` is absent or empty, check 2 still runs `make test-unit`
  (backward-compatible).
- No other check behavior is changed.

**Files:**
- Modify: `skills/verify/SKILL.md`

- [ ] **Step 1: Write failing test (RED)**

  Add to `tests/unit/test_verify_scoped_mode.py` inside `TestVerifyScopedMode`:

  ```python
  def test_check2_reuses_test_output_when_provided(self):
      text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
      assert "test_output" in text.split("### 2.")[1].split("### 3.")[0], \
          "Check 2 must reference test_output guard (reuse when provided, skip re-run)"
  ```

  Run: `make test-unit` — must FAIL (check 2 section has no `test_output` mention yet)

- [ ] **Step 2: Implement (GREEN)**

  Replace the check 2 section in `skills/verify/SKILL.md`:

  **Before:**
  ```markdown
  ### 2. ไม่มี regressions

  - Run the full suite, not just the new tests.
  - Compare pass count to the previous run — no unexpected changes.
  ```

  **After:**
  ```markdown
  ### 2. ไม่มี regressions

  - If `test_output` was provided and non-empty (from check 1 or caller):
    - Reuse it — do **not** run `make test-unit` again.
    - Parse pass count from `test_output` and compare to previous run.
    - If `test_output` contains `failed` or `error` → treat as regression.
  - If `test_output` is absent or empty → run the full suite:
    ```bash
    make test-unit
    ```
  - Compare pass count to the previous run — no unexpected changes.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the guard wording is consistent with the check 1 guard language in
  the `## Input` section (same terminology: "provided and non-empty").
  No structural changes needed.

  Run: `make test-unit` — still PASS
