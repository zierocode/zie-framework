---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-skills-registry-gaps.md
---

# Skills Registry Gaps in PROJECT.md — Design Spec

**Problem:** `zie-framework/PROJECT.md` documents commands and knowledge links
but omits all 10 skills in `skills/`, making them invisible to new contributors
reading the project hub.

**Approach:** Add a `## Skills` section to `PROJECT.md` listing all 10 skills
with their one-line purpose, modelled on the existing `## Commands` table.

**Components:**

- `zie-framework/PROJECT.md` — add Skills section

**Data Flow:**

1. Read each `skills/*/SKILL.md` to confirm names and purposes. The 10 skills
   are:
   - `spec-design` — draft design spec from backlog item
   - `spec-reviewer` — review spec for completeness and correctness
   - `write-plan` — convert approved spec into implementation plan
   - `plan-reviewer` — review plan for feasibility and test coverage
   - `tdd-loop` — RED/GREEN/REFACTOR loop for a single task
   - `impl-reviewer` — review implementation against spec and plan
   - `verify` — post-implementation verification gate
   - `test-pyramid` — test strategy advisor
   - `retro-format` — format retrospective findings as ADRs
   - `debug` — systematic bug diagnosis and fix path

2. Insert a `## Skills` section in `PROJECT.md` between `## Commands` and
   `## Knowledge`:

   ```markdown
   ## Skills

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

**Edge Cases:**

- Skills are invoked by commands, not users directly — table should note this
  (add a sub-heading note: "Invoked automatically by commands as subagents")
- New skills added in future must be manually added to this table; no
  auto-generation required (YAGNI)

**Out of Scope:**

- Updating `project/components.md` (that file has its own registry format)
- Adding skill parameter documentation to PROJECT.md
