---
tags: [chore]
---

# Refresh Stale Documentation (components.md, config-reference.md, README)

## Problem

- `components.md` references deleted hooks (stop-guard.py, compact-hint.py, sdlc-context.py) and renamed intent-detect.py. Last updated v1.21.0 — 8 versions behind.
- `config-reference.md` references deleted stop-guard.py
- README.md missing zie-release-mode agent from Agent Modes section
- README.md doesn't document `make implement-local`, `.zie/` directory, or `.zie/handoff.md`

## Motivation

Stale docs confuse contributors and new users. Deleted hook references make it impossible to understand the current architecture.

## Rough Scope

- Update components.md to reflect current hooks (remove stop-guard, compact-hint, sdlc-context; add stop-handler merged hooks; update intent-detect → intent-sdlc)
- Update config-reference.md to remove stop-guard references
- Add zie-release-mode to README Agent Modes
- Document `.zie/` directory and `make implement-local` in README
- Run `/resync` to update PROJECT.md knowledge hub