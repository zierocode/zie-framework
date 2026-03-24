---
approved: true
approved_at: 2026-03-24
backlog: backlog/retro-next-active-loop.md
---

# Retro → Next Active Loop — Design Spec

**Problem:** `/zie-retro` completes and stops with no transition back to the backlog. The developer must manually choose what to build next without any nudge from what was just learned in the retrospective.

**Approach:** Add a final step to `/zie-retro` that reads the Next lane of ROADMAP.md, surfaces 1–3 top candidates, and prints a clear suggested next action. Weighting: Critical-priority items ranked first, then items that align with pain points or themes identified in the retro write-up. Output is advisory — nothing is automatically started.

**Components:**
- Modify: `commands/zie-retro.md` — add "Suggest next" final step: read Next lane; rank by priority then retro-theme alignment; print top 1–3 candidates with `/zie-plan <slug>` prompt

**Acceptance Criteria:**
- [ ] Retro ends with a "Suggested next" block listing 1–3 Next lane candidates
- [ ] Critical-priority items appear before High, High before Medium
- [ ] Items that match pain points from the retro summary are ranked higher
- [ ] Output is a printed suggestion only — no automatic plan creation
- [ ] Graceful output when Next lane is empty: "Backlog is empty — add items with /zie-backlog"
- [ ] All existing retro steps and output unchanged

**Out of Scope:**
- Automatic plan creation or feature start
- Multi-item selection UI
- Dependency graph resolution for sequencing candidates
