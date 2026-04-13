---
tags: [feature]
---

# Pre-Computed Version Suggestion — at sprint start

## Problem

Version bump scans git log at release time; CHANGELOG draft reads git log again. Git log scanned 2×; semver logic runs under time pressure.

## Motivation

Sprint start computes suggested version from git log; store in .zie/sprint-state.json; release reuses. Faster release gate.

## Rough Scope

**In:**
- `commands/sprint.md` — compute version at sprint start
- `.zie/sprint-state.json` — store suggested version
- `commands/release.md` — read from state

**Out:**
- Version bump logic (unchanged)

<!-- priority: MEDIUM -->
<!-- depends_on: sprint-context-passthrough -->
