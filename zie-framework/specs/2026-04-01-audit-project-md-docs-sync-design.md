---
slug: audit-project-md-docs-sync
status: draft
date: 2026-04-01
---
# Spec: Add Missing docs-sync-check Row to PROJECT.md Skills Table

## Problem

`docs-sync-check` exists on disk at `skills/docs-sync-check/SKILL.md` and is
listed in `README.md`, but is absent from `zie-framework/PROJECT.md` skills
table. PROJECT.md is the internal knowledge hub — when a skill is missing from
that table the codebase map is stale and any agent relying on PROJECT.md for
skill discovery will have an incomplete view.

Additionally, the gap creates an ironic blind spot: `docs-sync-check` is the
skill responsible for flagging exactly this class of drift, yet it cannot flag
its own absence from PROJECT.md.

## Proposed Solution

1. Audit the full skills table in PROJECT.md against every `skills/*/SKILL.md`
   file on disk to confirm no other skills are missing.
2. Add a single row for `docs-sync-check` to the Skills table in
   `zie-framework/PROJECT.md` with an accurate purpose description.

This is a one-line docs fix. No skill content changes, no new skills, no
README changes.

## Acceptance Criteria

- [ ] AC1: Every directory under `skills/` that contains a `SKILL.md` has a
  corresponding row in the `zie-framework/PROJECT.md` Skills table.
- [ ] AC2: The `docs-sync-check` row is present in the Skills table with a
  purpose description that matches the skill's stated purpose in
  `skills/docs-sync-check/SKILL.md`.
- [ ] AC3: No existing rows in the Skills table are modified or removed.
- [ ] AC4: The Skills table remains alphabetically or logically ordered
  consistent with its current ordering convention.

## Out of Scope

- Changing the content of `skills/docs-sync-check/SKILL.md` or any other skill
- Adding new skills to the repo
- Updating `README.md` (tracked as a separate backlog item)
- Modifying hook, command, or agent registry entries
