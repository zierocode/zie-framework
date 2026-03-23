---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-skills-registry-gaps.md
spec: specs/2026-03-24-audit-skills-registry-gaps-design.md
---

# Skills Registry Gaps in PROJECT.md — Implementation Plan

**Goal:** Add a `## Skills` section to `zie-framework/PROJECT.md` listing all 10 skills with their one-line purpose so contributors can discover them from the project hub.
**Architecture:** Single new section inserted between `## Commands` and `## Knowledge` in `PROJECT.md`. The section mirrors the existing Commands table format. No code changes; content sourced from the 10 confirmed skills in `skills/`.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `zie-framework/PROJECT.md` | Insert Skills section between Commands and Knowledge |

## Task 1: Insert Skills section into PROJECT.md

**Acceptance Criteria:**
- `zie-framework/PROJECT.md` contains a `## Skills` section
- The section appears between `## Commands` and `## Knowledge`
- All 10 skills are listed with correct names and one-line purposes
- A note clarifies skills are invoked automatically by commands as subagents
- The table format matches the existing `## Commands` table style

**Files:**
- Modify: `zie-framework/PROJECT.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually by reading the file and confirming all 10 skills are listed with correct names.
  Run: `make test-unit` — existing tests pass

- [ ] **Step 2: Implement (GREEN)**
  In `zie-framework/PROJECT.md`, insert the following section between the `## Commands` table and the `## Knowledge` section:

  ```markdown
  ## Skills

  > Invoked automatically by commands as subagents — not called directly by users.

  | Skill | Purpose |
  | --- | --- |
  | spec-design | Draft design spec from backlog item |
  | spec-reviewer | Review spec for completeness and correctness |
  | write-plan | Convert approved spec into implementation plan |
  | plan-reviewer | Review plan for feasibility and test coverage |
  | tdd-loop | RED/GREEN/REFACTOR loop for a single task |
  | impl-reviewer | Review implementation against spec and plan |
  | verify | Post-implementation verification gate |
  | test-pyramid | Test strategy advisor |
  | retro-format | Format retrospective findings as ADRs |
  | debug | Systematic bug diagnosis and fix path |
  ```

  The 10 skill names confirmed from `skills/` directory:
  `debug`, `impl-reviewer`, `plan-reviewer`, `retro-format`, `spec-design`,
  `spec-reviewer`, `tdd-loop`, `test-pyramid`, `verify`, `write-plan`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify the section break between Commands and Skills, and between Skills and Knowledge, uses a single blank line consistent with the rest of the file.
  Run: `make test-unit` — still PASS
