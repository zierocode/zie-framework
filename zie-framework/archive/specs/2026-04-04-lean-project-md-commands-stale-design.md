---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-project-md-commands-stale.md
---

# Sync PROJECT.md + CLAUDE.md Commands and Skills Tables — Design Spec

**Problem:** PROJECT.md and CLAUDE.md contain stale registry tables — 4 commands are missing from the Commands table, the Skills table lists a deleted skill (`retro-format`) and omits two active skills (`load-context`, `reviewer-context`), making the primary onboarding doc 23% inaccurate and undermining discoverability.

**Approach:** Perform a surgical, pure-markdown edit on two files: (1) add `/sprint`, `/chore`, `/hotfix`, `/spike` to the Commands table in `PROJECT.md`; (2) replace `retro-format` with `load-context` and `reviewer-context` in the PROJECT.md Skills table; (3) add `/chore`, `/hotfix`, `/spike` to the SDLC Commands table in `CLAUDE.md` (which already has `/sprint`). No code changes, no hook changes — all edits are documentation-only table row additions/removals.

**Components:**
- `zie-framework/PROJECT.md` — Commands table (add 4 rows) + Skills table (remove 1 ghost row, add 2 rows)
- `CLAUDE.md` — SDLC Commands table (add 3 rows: `/chore`, `/hotfix`, `/spike`)

**Data Flow:**
1. Read `PROJECT.md` Commands table — identify missing commands vs `commands/` directory listing
2. Read `PROJECT.md` Skills table — identify ghost (`retro-format`) and missing entries vs `skills/*/SKILL.md` listing
3. Read `CLAUDE.md` SDLC Commands table — identify missing commands
4. Edit `PROJECT.md` Commands table: append rows for `/sprint`, `/chore`, `/hotfix`, `/spike` in logical order
5. Edit `PROJECT.md` Skills table: remove `retro-format` row, append `load-context` and `reviewer-context` rows
6. Edit `CLAUDE.md` SDLC Commands table: append rows for `/chore`, `/hotfix`, `/spike`
7. Verify: `commands/` file count == Commands table row count; `skills/*/SKILL.md` file count == Skills table row count

**Edge Cases:**
- `/sprint` already exists in CLAUDE.md SDLC table — add only the 3 missing commands, not all 4
- `retro-format` must be removed (not just marked deprecated) — the skill directory is already gone
- Row ordering should follow logical SDLC flow (full-pipeline commands together, maintenance tracks together)
- `docs-sync-check` skill does not validate PROJECT.md — this is out of scope for this item (separate backlog item noted in original backlog)

**Out of Scope:**
- Extending `docs-sync-check` to validate PROJECT.md (separate backlog item)
- Updating `project/components.md` registry (separate concern)
- Any README changes
- Any hook or command code changes
