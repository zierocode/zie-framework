---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-chore-git-add-A.md
---

# Lean Chore Git Add -A — Implementation Plan

**Goal:** Replace `git add -A` in `commands/chore.md` and `commands/implement.md` with targeted `git add` instructions and add a structural test that enforces this rule going forward.

**Architecture:** Two command markdown files are edited to replace blanket staging with explicit per-file staging. A new unit test file asserts that `git add -A` never appears in any `commands/*.md` file, catching regressions automatically. No Python hooks or config changes are needed.

**Tech Stack:** Python (pytest structural test), Markdown (command edits)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/chore.md` | Replace Step 4 `git add -A` with targeted git add + verification |
| Modify | `commands/implement.md` | Replace Step 4 `git add -A` with targeted git add for implementation files |
| Create | `tests/unit/test_no_git_add_A_in_commands.py` | Structural test: assert no `git add -A` in `commands/*.md` |

---

## Task 1: Add Structural Test (RED first)

**Acceptance Criteria:**
- `tests/unit/test_no_git_add_A_in_commands.py` exists
- Running `make test-unit` fails because `commands/chore.md` and `commands/implement.md` still contain `git add -A`
- Test scans only `commands/*.md` (not hooks/, not templates/, not Makefile)
- Test error message lists the violating file(s) and line(s)

**Files:**
- Create: `tests/unit/test_no_git_add_A_in_commands.py`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  """Structural test: no command file may use 'git add -A'.

  'git add -A' stages all untracked files, violating the CLAUDE.md Hard Rule
  that prohibits accidentally staging .env, credentials, or large binaries.
  All commands must use targeted git add with explicit file paths.

  Exempt from this check:
  - hooks/ (stop-guard.py nudge hint is a user-facing example string)
  - Makefile / templates/Makefile (human-invoked, intentional)
  """
  import re
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  COMMANDS_DIR = REPO_ROOT / "commands"


  def test_no_git_add_A_in_commands():
      """commands/*.md must not contain 'git add -A'."""
      pattern = re.compile(r'git add -A')
      violations = []
      for md_file in sorted(COMMANDS_DIR.glob("*.md")):
          content = md_file.read_text()
          for lineno, line in enumerate(content.splitlines(), 1):
              if pattern.search(line):
                  violations.append(f"{md_file.name}:{lineno}: {line.strip()}")
      assert not violations, (
          "commands/*.md must not use 'git add -A' — use targeted git add instead "
          "(CLAUDE.md Hard Rule: avoid accidentally staging .env / credentials):\n"
          + "\n".join(violations)
      )
  ```

  Run: `make test-unit` — must FAIL with violations in `chore.md` and `implement.md`

- [ ] **Step 2: Implement (GREEN)**
  No code to add — test is already written. GREEN comes after Tasks 2 and 3.

- [ ] **Step 3: Refactor**
  No refactor needed. Test is self-contained.

---

## Task 2: Fix commands/chore.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Step 4 of `/chore` no longer contains `git add -A`
- Step 4 instructs: use `git diff --name-only HEAD` to identify modified tracked files, then `git add <specific files>`
- Step 4 includes pre-commit verification: inspect `git status` before committing
- New untracked files instruction: use `git add <path>` explicitly, never `git add -A`
- Structural test from Task 1 passes for `chore.md`

**Files:**
- Modify: `commands/chore.md`

- [ ] **Step 1: Write failing test (RED)**
  Task 1 test already covers this. Confirm `make test-unit` fails citing `chore.md`.

- [ ] **Step 2: Implement (GREEN)**

  In `commands/chore.md`, replace Step 4:

  **Before:**
  ```markdown
  4. **Commit** — `git add -A && git commit -m "chore: <slug>"`
  ```

  **After:**
  ```markdown
  4. **Commit** — Stage only files changed in this chore, then commit:
     ```
     git diff --name-only HEAD   # list modified tracked files
     git add <file1> <file2> …   # stage those files explicitly
     # For new untracked files: git add <path> — never git add -A
     git status                  # verify only intended files are staged
     git commit -m "chore: <slug>"
     ```
  ```

  Run: `make test-unit` — `test_no_git_add_A_in_commands` must now PASS for `chore.md`

- [ ] **Step 3: Refactor**
  Read the full `commands/chore.md` after edit. Confirm wording is consistent with the command's "keep chores small" ethos. No other changes needed.

---

## Task 3: Fix commands/implement.md

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Step 4 of `## When All Tasks Complete` in `/implement` no longer contains `git add -A`
- Step 4 instructs: stage implementation files + `zie-framework/ROADMAP.md` explicitly
- `git reset HEAD` rollback instruction preserved for the ❌ Issues Found path
- Structural test from Task 1 passes for `implement.md`

**Files:**
- Modify: `commands/implement.md`

- [ ] **Step 1: Write failing test (RED)**
  Task 1 test already covers this. Confirm `make test-unit` fails citing `implement.md`.

- [ ] **Step 2: Implement (GREEN)**

  In `commands/implement.md`, the `## When All Tasks Complete` section Step 4:

  **Before:**
  ```markdown
  4. `git add -A` → collect verify result:
     - ✅ APPROVED → commit
     - ❌ Issues Found → `git reset HEAD`, fix, re-verify, re-stage
  ```

  **After:**
  ```markdown
  4. Stage changed files explicitly → collect verify result:
     ```
     git add $(git diff --name-only HEAD) zie-framework/ROADMAP.md
     # Review git status before committing
     ```
     - ✅ APPROVED → commit
     - ❌ Issues Found → `git reset HEAD`, fix, re-verify, re-stage
  ```

  Run: `make test-unit` — all three files now clear; `test_no_git_add_A_in_commands` must PASS

- [ ] **Step 3: Refactor**
  Read the full `## When All Tasks Complete` section. Confirm the verify-then-commit flow still reads correctly. Confirm `git reset HEAD` rollback path unchanged.

---

## Task 4: Full Test Suite Pass

<!-- depends_on: Task 2, Task 3 -->

**Acceptance Criteria:**
- `make test-unit` exits 0 with no failures
- `make lint` exits 0 (new test file passes ruff)
- `test_no_git_add_A_in_commands` is present in the test output
- No regressions in existing command tests (test_claude_md_commands, test_docs_sync, etc.)

**Files:**
- No new files

- [ ] **Step 1: Write failing test (RED)**
  N/A — this is a verification task.

- [ ] **Step 2: Run full suite (GREEN)**
  ```
  make lint
  make test-unit
  ```
  Expected: all pass, including new structural test.

- [ ] **Step 3: Refactor**
  If any existing test fails due to command edits (e.g. test_claude_md_commands.py), update the test assertions to match the new wording. Never revert the fix — only update tests to reflect the correct behavior.
