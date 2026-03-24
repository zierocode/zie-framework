---
approved: false
approved_at: ~
backlog: backlog/verify-scoped-mode.md
spec: specs/2026-03-24-verify-scoped-mode-design.md
---

# verify Skill Scoped Mode — Implementation Plan

**Goal:** Add a `scope` parameter to the `verify` skill so callers can request a lightweight `tests-only` check instead of always running all 5 checks. Update `/zie-fix` to explicitly pass `scope=tests-only`.
**Architecture:** Pure markdown edits — no Python hooks or new files. The `scope` parameter is declared in the skill's invocation interface and branched in the checklist body. `/zie-fix` passes the parameter as a keyword argument in the `Skill()` call.
**Tech Stack:** Markdown (skill + command definitions), pytest + `Path.read_text()` (validation)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/verify/SKILL.md` | Add `scope` parameter; add `tests-only` conditional branch |
| Modify | `commands/zie-fix.md` | Pass `scope=tests-only` to `Skill(zie-framework:verify)` |
| Create | `tests/unit/test_verify_scoped_mode.py` | Validate both files contain required text |

---

## Task 1: Add `scope` parameter to `skills/verify/SKILL.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/verify/SKILL.md` declares a `scope` parameter with values `full` (default) and `tests-only`
- A `tests-only` conditional branch is present in the checklist body
- `tests-only` branch runs: check 1 (tests), check 2 (no regressions), secrets scan only from check 4
- `tests-only` branch skips: check 3 (TODOs), full code review portion of check 4, check 5 (docs sync)
- `scope=full` behavior is unchanged — all 5 checks run as before
- Default scope is `full` when caller does not specify

**Files:**
- Modify: `skills/verify/SKILL.md`
- Create: `tests/unit/test_verify_scoped_mode.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_verify_scoped_mode.py
  from pathlib import Path

  SKILLS_DIR = Path(__file__).parents[2] / "skills"
  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  class TestVerifyScopedMode:
      def test_scope_parameter_declared(self):
          text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
          assert "scope" in text, \
              "verify SKILL.md must declare a scope parameter"

      def test_tests_only_branch_present(self):
          text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
          assert "tests-only" in text, \
              "verify SKILL.md must contain a tests-only branch"

      def test_full_scope_default_declared(self):
          text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
          assert "full" in text, \
              "verify SKILL.md must declare full as a scope value"
  ```
  Run: `make test-unit` — must FAIL (`scope` and `tests-only` not yet in file)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/verify/SKILL.md`, add the following parameter block immediately after the `argument-hint` line in the frontmatter, and add the scoped-mode conditional section to the checklist body.

  **Frontmatter addition** — replace the existing `argument-hint: ""` line with:
  ```yaml
  argument-hint: "scope=full|tests-only (default: full)"
  ```

  **Body addition** — insert a new section directly before `## รายการตรวจสอบ`:
  ```markdown
  ## Parameters

  | Parameter | Values | Default | Description |
  | --- | --- | --- | --- |
  | `scope` | `full`, `tests-only` | `full` | Controls which checks run. `tests-only` runs checks 1, 2, and secrets scan from 4 only — skips TODOs (3), full code review (4), and docs sync (5). |

  ## Scope: tests-only

  When called with `scope=tests-only`, run only:

  1. **Check 1** — ตรวจ Tests (full, as below)
  2. **Check 2** — ไม่มี regressions (full, as below)
  3. **Check 4 — secrets scan only:** Are secrets or credentials in the code? → STOP, remove immediately. Skip all other check 4 items.

  Skip check 3 (TODOs), skip the remainder of check 4 (design match, simplifications), and skip check 5 (docs sync entirely).

  Print a scoped verification summary:

  ```text
  Verification complete (scope: tests-only):

  Tests   : unit ✓ | integration ✓|n/a | e2e ✓|n/a
  Secrets : none detected

  Scope was tests-only — docs sync and full code review skipped.
  ```

  When called with `scope=full` or with no scope argument → run all 5 checks as documented below.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read the full `skills/verify/SKILL.md` to confirm: existing check 1–5 bodies are untouched, the new `## Parameters` table is well-formed, the `## Scope: tests-only` section is clear and unambiguous about what is skipped.
  Run: `make test-unit` — still PASS

---

## Task 2: Update `commands/zie-fix.md` to pass `scope=tests-only`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/zie-fix.md` passes `scope=tests-only` explicitly in the `Skill(zie-framework:verify)` invocation
- No other logic in `zie-fix.md` is changed

**Files:**
- Modify: `commands/zie-fix.md`
- Modify: `tests/unit/test_verify_scoped_mode.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_verify_scoped_mode.py — add new class after TestVerifyScopedMode

  class TestZieFixScopeParam:
      def test_zie_fix_passes_scope_tests_only(self):
          text = (COMMANDS_DIR / "zie-fix.md").read_text()
          assert "scope=tests-only" in text, \
              "zie-fix.md must pass scope=tests-only to Skill(zie-framework:verify)"
  ```
  Run: `make test-unit` — must FAIL (`scope=tests-only` not yet in `zie-fix.md`)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-fix.md`, under the `### ยืนยันว่าแก้ถูกต้อง` section, replace the current verify invocation line:

  Before:
  ```
  1. Invoke `Skill(zie-framework:verify)` with scope = tests only (bug fixes
     do not require full docs-sync check).
  ```

  After:
  ```
  1. Invoke `Skill(zie-framework:verify)` with `scope=tests-only` (bug fixes
     do not require full docs-sync check or code review).
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read the full `commands/zie-fix.md` to confirm: all other steps, the pre-check block, the bug-understanding flow, the regression test step, the memory/learning step, and the summary print block are unchanged.
  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/verify/SKILL.md commands/zie-fix.md tests/unit/test_verify_scoped_mode.py && git commit -m "feat: verify-scoped-mode"`*
