# Smarter Framework Intelligence

## Problem

The framework is stateless between sessions — it doesn't learn from past cycles,
can't proactively warn about drift, and treats every project the same regardless
of history. Users must manually observe velocity, coverage trends, and backlog health.

## Motivation

A solo dev framework that learns from its own usage becomes progressively more
valuable. Proactive nudges reduce the mental overhead of self-management. Velocity
data makes estimation realistic. Self-tuning reduces the need to manually adjust
config over time.

## Rough Scope

**In:**
- **Velocity tracking** — measure cycle time per feature from git history, show
  trend in `/zie-status`
- **Proactive nudges** — Stop hook surfaces warnings: RED phase too long, coverage
  drop, stale backlog items
- **Backlog intelligence** — auto-tag items (bug/feature/chore/debt), detect
  duplicates before creation
- **Self-tuning proposals** — after retro, framework proposes `.config` changes
  based on observed patterns; user approves

**Out:** External integrations, multi-project analytics, ML models.
