# ADR-050 — Escape Hatch Options Over Hard Block for No-Track State

**Status:** Accepted
**Date:** 2026-04-04

## Context

When `intent-sdlc.py` detects an implement/fix intent but no active backlog→spec→plan
track is open, the previous implementation hard-blocked with ⛔ STOP. This caused
friction for legitimate non-pipeline workflows like hotfixes, spikes, and chores.

## Decision

Changed the no-track response from a hard ⛔ STOP to an informational nudge listing
four options:
- standard: `/backlog` → `/spec` → `/plan` → `/implement`
- hotfix: `/hotfix`
- spike: `/spike`
- chore: `/chore`

The hook still surfaces the nudge but does not block Claude from proceeding. The
`is_track_active(cwd)` check now also considers open drift log entries (not just ROADMAP
Now lane) so hotfix/spike/chore tracks are recognized as active.

## Consequences

**Positive:**
- Preserves workflow guidance without blocking legitimate use cases
- Escape hatch commands now have a discoverable entry point
- `is_track_active` reflects real activity (drift log + ROADMAP), not just formal pipeline

**Negative:**
- Weaker enforcement: users can ignore the nudge and proceed without a track
- Harder to audit "how often was pipeline bypassed" (now voluntary)

**Neutral:**
- Drift log still records bypass events for retro analysis

## Alternatives Considered

- **Keep hard block**: Too restrictive for a solo-dev context where hotfixes are common
- **No nudge at all**: Loses discoverability of escape hatch commands
