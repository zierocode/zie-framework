---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-project-md-commands-stale.md
---

# Sync PROJECT.md + CLAUDE.md Commands and Skills Tables — Implementation Plan

**Goal:** Add 4 missing commands and fix 3 skill rows across PROJECT.md and CLAUDE.md so the registry tables exactly match the repo contents.
**Architecture:** Pure markdown table edits — no code, no hooks, no tests required. Two files modified, three independent edit operations.
**Tech Stack:** Markdown (Edit tool), verification via Glob/Grep counts.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `zie-framework/PROJECT.md` | Add 4 command rows + remove retro-format + add 2 skill rows |
| Modify | `CLAUDE.md` | Add 3 command rows (/chore, /hotfix, /spike) |

---

## Task 1: Add missing commands to PROJECT.md Commands table

<!-- depends_on: none -->

**Acceptance Criteria:**
- PROJECT.md Commands table contains `/sprint`, `/chore`, `/hotfix`, `/spike`
- Row count in Commands table equals file count in `commands/` directory (15)
- Ordering: full-pipeline commands first, then maintenance tracks (`/sprint`, `/chore`, `/hotfix`, `/spike`) grouped after `/audit`

**Files:**
- Modify: `zie-framework/PROJECT.md`

- [ ] **Step 1: Write failing test (RED)**

  Grep confirms all 4 commands are absent:

  ```bash
  grep -c "sprint\|chore\|hotfix\|spike" zie-framework/PROJECT.md
  # Expected: 0 matches in Commands table section
  ```

  Count commands/ files:
  ```bash
  ls commands/*.md | wc -l
  # Expected: 15
  ```

  Count PROJECT.md Commands rows:
  ```bash
  grep -c "^| /" zie-framework/PROJECT.md
  # Expected: 10 (currently 10 rows, missing 4 = FAIL)
  ```

- [ ] **Step 2: Implement (GREEN)**

  Edit `zie-framework/PROJECT.md` — append 4 rows to the Commands table after the `| /audit |` row:

  ```markdown
  | /sprint | Sprint clear — batch all items through full pipeline (spec→plan→implement→release→retro) |
  | /chore | Maintenance task track — no spec required |
  | /hotfix | Emergency fix track — describe → fix → ship without full pipeline |
  | /spike | Time-boxed exploration in an isolated sandbox directory |
  ```

  Verify row count matches:
  ```bash
  grep -c "^| /" zie-framework/PROJECT.md
  # Expected: 14 (10 existing + 4 added)
  ```

  Note: `commands/` has 15 files (including `init.md`). `init.md` maps to `/init` which is already excluded from PROJECT.md Commands table (init is a bootstrap-only command not part of the daily SDLC loop). Count of 14 table rows vs 14 daily-use commands is correct — verify exclusion is intentional.

- [ ] **Step 3: Refactor**

  Confirm logical ordering is correct (SDLC flow → maintenance tracks → ops).
  No code cleanup needed.

---

## Task 2: Fix PROJECT.md Skills table — remove ghost, add actives

<!-- depends_on: none -->

**Acceptance Criteria:**
- `retro-format` row is removed from Skills table
- `load-context` row is present in Skills table
- `reviewer-context` row is present in Skills table
- Skills table row count equals count of `skills/*/SKILL.md` files (13)

**Files:**
- Modify: `zie-framework/PROJECT.md`

- [ ] **Step 1: Write failing test (RED)**

  Confirm ghost exists and actives are missing:
  ```bash
  grep "retro-format" zie-framework/PROJECT.md
  # Expected: 1 match (ghost present — FAIL)

  grep "load-context" zie-framework/PROJECT.md
  # Expected: 0 matches (missing — FAIL)

  grep "reviewer-context" zie-framework/PROJECT.md
  # Expected: 0 matches (missing — FAIL)
  ```

  Count skills files:
  ```bash
  ls skills/*/SKILL.md | wc -l
  # Expected: 13
  ```

- [ ] **Step 2: Implement (GREEN)**

  Edit `zie-framework/PROJECT.md`:
  1. Remove the `retro-format` row:
     ```markdown
     | retro-format | Format retrospective findings as ADRs |
     ```
  2. Append two rows to the Skills table (after `docs-sync-check` row):
     ```markdown
     | load-context | Load shared context bundle (ADRs + project context) for reviewer skills |
     | reviewer-context | Load reviewer context (ADRs + ROADMAP) for spec/plan/impl reviewer skills |
     ```

  Verify:
  ```bash
  grep "retro-format" zie-framework/PROJECT.md
  # Expected: 0 matches (ghost removed — PASS)

  grep "load-context\|reviewer-context" zie-framework/PROJECT.md
  # Expected: 2 matches (actives present — PASS)
  ```

- [ ] **Step 3: Refactor**

  No additional cleanup. Confirm Skills table note ("Invoked automatically by commands as subagents") still renders correctly above the updated table.

---

## Task 3: Add missing commands to CLAUDE.md SDLC Commands table

<!-- depends_on: none -->

**Acceptance Criteria:**
- CLAUDE.md SDLC Commands table contains `/chore`, `/hotfix`, `/spike`
- `/sprint` row is NOT duplicated (it already exists)
- Table remains logically ordered

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing test (RED)**

  Confirm `/sprint` exists, others are missing:
  ```bash
  grep "sprint\|chore\|hotfix\|spike" CLAUDE.md
  # Expected: sprint = 1 match, chore/hotfix/spike = 0 matches (FAIL for 3 missing)
  ```

- [ ] **Step 2: Implement (GREEN)**

  Edit `CLAUDE.md` SDLC Commands table — append 3 rows after the `/sprint` row:

  ```markdown
  | `/chore` | Maintenance task track — no spec required |
  | `/hotfix` | Emergency fix track — describe → fix → ship without full pipeline |
  | `/spike` | Time-boxed exploration in an isolated sandbox |
  ```

  Verify:
  ```bash
  grep "chore\|hotfix\|spike" CLAUDE.md
  # Expected: 3 matches (PASS)

  grep -c "sprint" CLAUDE.md
  # Expected: 1 (no duplicate — PASS)
  ```

- [ ] **Step 3: Refactor**

  No cleanup needed. Confirm SDLC Commands table header and footer lines are intact.

---

## Verification

After all 3 tasks complete, run a final cross-check:

```bash
# Commands table rows
grep -c "^| /" zie-framework/PROJECT.md

# Skills table: no ghost, actives present
grep "retro-format" zie-framework/PROJECT.md  # must be empty
grep "load-context" zie-framework/PROJECT.md   # must match
grep "reviewer-context" zie-framework/PROJECT.md  # must match

# CLAUDE.md: all 4 commands present
grep "sprint\|chore\|hotfix\|spike" CLAUDE.md  # must be 4 matches
```
