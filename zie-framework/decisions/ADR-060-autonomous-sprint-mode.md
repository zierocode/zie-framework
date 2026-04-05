---
adr: 060
title: Autonomous Sprint Mode
status: Accepted
date: 2026-04-06
---

# ADR-060 — Autonomous Sprint Mode

## Status

Accepted

## Context

The standard `/sprint` workflow requires user gates at spec review, plan review,
and retro confirmation. For batch sprints (many backlog items queued), these gates
force the user to remain present throughout, defeating the value of batch processing.

## Decision

Add `autonomous_mode=true` context flag to `/sprint`. When set:
- Clarity detection scores each backlog item (0–3 scale); ≥2 → direct spec, <2 → ask 1 question
- Reviewers (spec, plan, impl) run inline via Skill() without surfacing results for approval
- Auto-fix protocol: 1 retry before interrupt
- Retro auto-runs after release with no prompt
- Only 3 cases interrupt user: vague backlog (clarity <2 after question), auto-fix failure after 1 retry, dependency conflict

## Consequences

**Positive:** Fully unattended sprint from backlog → release → retro. User can
queue items and return to a completed sprint.

**Negative:** Reduced visibility into intermediate decisions. Wrong spec/plan
assumptions won't surface until implementation fails.

**Neutral:** Autonomous mode is opt-in. Non-autonomous behavior unchanged.

## Alternatives

User gates at every phase — current behavior, retained for non-autonomous mode.
LLM-judge for clarity — rejected as overkill; simple 3-criterion scoring sufficient.
