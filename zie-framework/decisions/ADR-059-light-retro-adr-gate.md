---
adr: 059
title: Light Retro — ADR Writing Gated on Plan Tag
status: Accepted
date: 2026-04-06
---

# ADR-059 — Light Retro — ADR Writing Gated on Plan Tag

## Status

Accepted

## Context

Full retro writes ADRs for every sprint regardless of whether any lasting
architectural decisions were made. Routine sprints (chores, small fixes, token
optimizations) generate ADRs with little content, increasing noise in the
decisions/ directory and retro wall-clock time.

## Decision

Gate full ADR writing on `<!-- adr: required -->` tag in the shipped plan file.
If tag absent: skip full ADR writing, append only a one-line summary to
`ADR-000-summary.md`. If tag present: full ADR writing proceeds as before.

## Consequences

**Positive:** ~80% reduction in retro overhead for routine sprints. ADRs
only created when decisions have lasting architectural impact.

**Negative:** Requires author discipline to add the tag when appropriate.
Decisions could be missed if tag is forgotten.

**Neutral:** ADR-000-summary.md still updated every release for traceability.

## Alternatives

Always write full ADRs — rejected due to noise-to-signal ratio degradation.
Auto-detect decisions from commit messages — rejected due to false positive risk.
