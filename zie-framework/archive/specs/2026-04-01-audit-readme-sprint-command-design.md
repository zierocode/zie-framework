---
slug: audit-readme-sprint-command
status: approved
date: 2026-04-01
---
# Spec: Add /zie-sprint to README.md Commands Table

## Problem

`/zie-sprint` was added in v1.15.0 and is documented in `CLAUDE.md` and
`zie-framework/PROJECT.md`, but it is entirely absent from the README.md
Commands table — the primary public-facing documentation for plugin consumers.

A developer discovering the plugin via README.md has no visibility into the
sprint-clear batch pipeline command, creating a gap between what the plugin
can do and what is discoverable.

## Proposed Solution

Add a single row for `/zie-sprint` to the Commands table in `README.md`, in
the correct position (after `/zie-retro`, before `/zie-fix`), matching the
table's existing column structure (`Command | Stage | Description`).

Row to add:

| `/zie-sprint` | Batch | Sprint clear — batch all items through full pipeline (spec→plan→implement→release→retro) |

No other files require changes — `CLAUDE.md` already lists `/zie-sprint` in
its SDLC Commands table, and the command file at `commands/zie-sprint.md`
already exists.

## Acceptance Criteria

- [ ] AC1: `README.md` Commands table contains a row for `/zie-sprint`
- [ ] AC2: The `/zie-sprint` row is positioned after `/zie-retro` and before `/zie-fix`
- [ ] AC3: The row's Description column reads: "Sprint clear — batch all items through full pipeline (spec→plan→implement→release→retro)"
- [ ] AC4: The row's Stage column is "Batch" (consistent with its cross-stage nature)
- [ ] AC5: All other existing rows in the Commands table are unchanged
- [ ] AC6: All commands in `commands/zie-*.md` are listed in README.md Commands table (verified by manual grep)

## Out of Scope

- Changes to `CLAUDE.md` (already up to date)
- Changes to `commands/zie-sprint.md` or any other command file
- Changes to the Pipeline diagram in README.md
- Adding `/zie-sprint` to the Pipeline stage table (it is a meta-command spanning all stages, not a single pipeline stage)
- Any hook or test changes
