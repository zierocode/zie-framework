# Workflow Enforcement and Escape Hatches

## Problem

Users can currently bypass the SDLC pipeline entirely — editing files directly,
pushing without gates, deploying ad-hoc. The framework guides but does not enforce,
making SDLC compliance dependent on discipline rather than structure.

## Motivation

The pipeline only has value if it's consistently followed. Enforcement makes the
workflow a contract, not a suggestion. But hard blocks create friction — the solution
is structured escape hatches that keep users inside the framework while accommodating
real urgency: hotfixes, experiments, maintenance tasks.

## Rough Scope

**In:**
- PreToolUse hook intercepts direct file edits when no active feature exists →
  proposes appropriate workflow track instead of blocking
- New workflow tracks: `hotfix` (describe → fix → ship), `spike` (sandbox, no
  ROADMAP entry), `chore` (lightweight, no spec required)
- Drift log: audit trail of bypass events with reason
- `/zie-status` shows drift event count

**Out:** Hard blocking (exit 2) — always offer an alternative, never dead-end the user.
