---
approved: true
approved_at: 2026-03-24
backlog: backlog/roadmap-section-aware-reads.md
---

# ROADMAP.md Section-Aware Reads — Design Spec

**Problem:** Every command reads all of ROADMAP.md — Done history, Later/Icebox, and full backlog — even when only one section is needed. `/zie-implement` needs only Now. `/zie-status` needs Now + counts. As ROADMAP.md grows, wasted reads compound on every invocation.

**Approach:** Map each command to its minimum required sections and replace full file reads with targeted section reads. Implementation: read lines until the next `---` separator after the target heading (e.g., read `## Now` section only by stopping at the next `---`). Use Grep with offset/limit or targeted Read with line ranges derived from section markers.

**Components:**
- Modify: `commands/zie-implement.md` — read Now section only (stop at next `---`)
- Modify: `commands/zie-status.md` — read Now section fully; use line-count grep for Next/Done counts
- Modify: `commands/zie-plan.md` — read Now (WIP check) + Next (item selection)
- Modify: `commands/zie-spec.md` — read Now section only (WIP check)
- Modify: `commands/zie-retro.md` — read Now + Done (recent, last ~20 lines)
- Modify: `commands/zie-release.md` — read Now section only

**Acceptance Criteria:**
- [ ] `/zie-implement` loads Now lane only — not Done history or Later items
- [ ] `/zie-status` shows Next/Done counts without loading full content of those sections
- [ ] Each command reads only its mapped sections per the scope above
- [ ] ROADMAP.md file format and content unchanged
- [ ] Commands remain correct when ROADMAP has no active feature (empty Now lane)

**Out of Scope:**
- Changing ROADMAP.md format or section structure
- Lazy loading of plan files (see plan-lazy-loading)
