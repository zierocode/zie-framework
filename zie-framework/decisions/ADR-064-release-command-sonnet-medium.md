---
adr: 064
title: Release Command Upgraded to Sonnet/Medium
status: Accepted
date: 2026-04-13
---

# ADR-064 — Release Command Upgraded to Sonnet/Medium

## Context

`commands/release.md` was set to `model: haiku` + `effort: low` under ADR-030
(haiku default, sonnet escalation via inline comments). In practice, `/release`
is most often invoked immediately after a long `/sprint` or `/implement` session.
Haiku's smaller context window fills up from the preceding session, causing an
immediate "Context limit reached" error before the release gates even start.

Additionally, release is a 10-step multi-stage operation (gates, version bump,
CHANGELOG, merge, tag, archive) — not a mechanical checklist task. Haiku is
appropriate for single-step or checklist tasks; release requires coordination and
judgment across many steps.

## Decision

Upgrade `commands/release.md` to `model: sonnet` + `effort: medium`.

Inline `<!-- model: sonnet -->` escalation comments on Steps 1 and 5 are
retained (they remain valid and can serve as documentation of judgment-heavy
steps).

## Consequences

- `/release` no longer fails with context-limit errors after long sprint sessions.
- Slightly higher token cost per release invocation (sonnet vs haiku), accepted
  because release runs at most once per sprint cycle.
- Mirrors ADR-017 (impl-review upgraded from haiku to sonnet for the same
  reasoning-quality rationale).
