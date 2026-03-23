---
approved: true
approved_at: 2026-03-23
backlog: backlog/reviewer-depth.md
reviewed_iterations: 2
---

# Reviewer Depth — Design Spec

**Problem:** The spec-reviewer, plan-reviewer, and impl-reviewer skills review
documents in isolation — no project context, no codebase, no ADRs, no ROADMAP.
This makes reviews superficial: a spec can be approved even if it conflicts with
an existing decision, targets files that don't exist, or duplicates work already
planned elsewhere.

**Approach:** Each reviewer loads a context bundle before reviewing. The bundle
is assembled by reading three sources: (1) relevant codebase files named in the
spec/plan, (2) existing ADRs and retro learnings from `zie-framework/decisions/`
and `project/context.md`, (3) ROADMAP active + ready items. The reviewer then
cross-references its checklist against this context. The bundle is lightweight —
read only what is named, not a full codebase scan.

**Components:**

- `skills/spec-reviewer/SKILL.md` — add context bundle step + 3 new checks
- `skills/plan-reviewer/SKILL.md` — add context bundle step + 3 new checks
- `skills/impl-reviewer/SKILL.md` — add context bundle step + 3 new checks

**Context Bundle (same for all three reviewers):**

```
1. Files named in spec/plan Components section
   → Read each file if it exists; note "FILE NOT FOUND" if missing
2. zie-framework/decisions/*.md  (all ADR files)
3. zie-framework/project/context.md  (design context snapshot)
4. zie-framework/ROADMAP.md  (Now + Ready + Next lanes only)
```

**New Checks added to each reviewer:**

| Check | spec-reviewer | plan-reviewer | impl-reviewer |
| --- | --- | --- | --- |
| Files exist in codebase | named components exist | named files in file map exist | modified files exist |
| No ADR conflict | spec decisions don't contradict ADRs | plan approach matches ADRs | impl doesn't violate ADRs |
| No ROADMAP conflict | not duplicate of Ready/Now item | not duplicate of Ready/Now item | — |
| Codebase pattern match | — | planned approach matches existing patterns | implementation matches patterns |

**Data Flow:**

```
reviewer invoked with (spec_path, [plan_path], [impl_path])

  Phase 1 — Load context bundle:
    a. Parse Components/File Map section → extract file paths
    b. Read each named file (skip gracefully if missing, note it)
    c. Read zie-framework/decisions/*.md
    d. Read zie-framework/project/context.md (if exists)
    e. Read zie-framework/ROADMAP.md (Now + Ready + Next only)

  Phase 2 — Run existing checklist (unchanged)

  Phase 3 — Run new context checks:
    - File existence: list any named files that don't exist
    - ADR conflict: flag any approach that contradicts a decision in decisions/
    - ROADMAP conflict: flag if a spec/plan overlaps a Ready or Now item
    - Pattern match (plan/impl only): flag if approach diverges from patterns
      observed in the read files — surface the divergence for Zie to accept
      or reject (reviewer notes, does not decide)

  Phase 4 — Verdict (same format as before, new checks surfaced as issues)
```

**Edge Cases:**

- `decisions/` empty or missing → skip ADR check, note "No ADRs found"
- `project/context.md` missing → skip context check, note "No context doc"
- Named file in spec doesn't exist yet (new file to be created) → not a
  failure; reviewer should check if the spec marks it as "Create" vs "Modify"
- ROADMAP missing → skip ROADMAP conflict check
- Bundle read fails for any file → log and continue (never block review)

**Out of Scope:**

- Full codebase scan (only read files explicitly named in spec/plan)
- Running tests or linters as part of review
- Automatic conflict resolution
- Reviewing files not named in the document under review
