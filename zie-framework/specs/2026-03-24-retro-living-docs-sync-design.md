---
approved: true
approved_at: 2026-03-24
backlog: backlog/retro-living-docs-sync.md
---

# Retro Living Docs Sync — Design Spec

**Problem:** `CLAUDE.md` and `README.md` drift from the actual codebase after releases. `/zie-retro` updates `project/components.md` and `project/architecture.md` but never touches top-level docs. The `/zie-release` docs gate only catches obvious cases and relies on Claude's judgment rather than systematic extraction.

**Approach:** Add a systematic docs sync step to `/zie-retro` (Option A: integrate into the existing "update project knowledge" step). The step reads `CLAUDE.md` and `README.md`, extracts current codebase state (commands, hooks, skills, tech stack, build commands), and updates any sections that no longer match actuals. The comparison is structural (actual vs. documented) not judgment-based.

**Components:**
- Modify: `commands/zie-retro.md` — add docs sync step within or after "update project knowledge": read `CLAUDE.md` + `README.md`; compare against actual `commands/`, `hooks/`, `skills/` directory contents and `VERSION`; update any stale sections; log what was changed

**Acceptance Criteria:**
- [ ] Retro updates `CLAUDE.md` and `README.md` in the same session (not in a separate run)
- [ ] Comparison is structural: enumerate actual commands/hooks/skills vs. what docs say
- [ ] Updates are applied systematically — not based on "seems right" judgment
- [ ] Changes logged in retro output ("Updated CLAUDE.md: added X, removed Y")
- [ ] Step runs even when there are no changes to log ("CLAUDE.md in sync")
- [ ] No real-time doc updates triggered during `/zie-implement`

**Out of Scope:**
- Real-time documentation updates during feature implementation (too noisy)
- Triggering `/zie-resync` automatically (Option B deferred — Option A implemented first)
