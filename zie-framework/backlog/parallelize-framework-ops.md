---
id: parallelize-framework-ops
title: Parallelize audit, test gates, and retro phases
priority: medium
created: 2026-03-27
source: deep-analysis-2026-03-27
---

## Problem

Several multi-step framework operations run serially that could safely run in parallel:
1. `/zie-audit` — 9 dimensions run one-by-one (security, code health, structure, etc.)
2. Test gate — unit + integration + md lint run sequentially in Makefile
3. `/zie-retro` — ADR write + ROADMAP update + brain store run in sequence

## Motivation

Parallelizing independent operations directly reduces wall-clock time for the most expensive
framework commands. `/zie-audit` in particular is slow due to serial WebSearch calls.

## Acceptance Criteria

- [ ] `/zie-audit` groups dimensions into ≤3 parallel agents (e.g., security+code / structure+docs / standards+test)
- [ ] `make test` runs unit + integration in parallel (where pytest allows)
- [ ] `/zie-retro` ADR write and ROADMAP update launched in parallel, brain store after
- [ ] No race conditions: parallel writes target different files
- [ ] Measured speed improvement documented (approximate wall-clock before/after)

## Scope

- `commands/zie-audit.md` (if exists) or `skills/zie-audit/SKILL.md`
- `Makefile` — parallel test targets
- `commands/zie-retro.md`
