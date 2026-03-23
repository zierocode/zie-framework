---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-zieinit-deprecated-filename.md
spec: specs/2026-03-24-audit-zieinit-deprecated-filename-design.md
---

# zie-init Deprecated Filename Reference — Implementation Plan

**Goal:** Replace the two occurrences of `decisions.md` with `context.md` in the Step 3 directory tree inside `commands/zie-init.md`.
**Architecture:** Surgical two-line fix in a Markdown code block — no logic, no templates, no Python changes. The surrounding file is otherwise correct; lines 87 and 231 already use `context.md`. Only the directory tree diagram at lines ~215 is wrong.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-init.md` | Replace `decisions.md` with `context.md` in Step 3 directory tree |

## Task 1: Fix deprecated filename reference in zie-init.md directory tree

**Acceptance Criteria:**
- `commands/zie-init.md` contains no occurrence of `decisions.md`
- The Step 3 directory tree shows `context.md` as the third spoke under `project/`
- All other references in the file (lines 87, 231) are confirmed correct and unchanged
- `make test-unit` passes (existing docs standards tests do not regress)

**Files:**
- Modify: `commands/zie-init.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually with a grep:
  `grep -n "decisions.md" commands/zie-init.md` — must show the stale lines before fix, empty after fix.
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-init.md` Step 3 directory tree (around line 215), change:

  ```text
  │   └── decisions.md
  ```

  to:

  ```text
  │   └── context.md
  ```

  Confirm with grep after edit: `grep -n "decisions.md" commands/zie-init.md` returns empty.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify line 231 references `project/context.md` (already correct per spec).
  Verify `templates/project/` contains `context.md.template` and no `decisions.md.template`.
  No code changes expected; this step is a confirmation pass.
  Run: `make test-unit` — still PASS
