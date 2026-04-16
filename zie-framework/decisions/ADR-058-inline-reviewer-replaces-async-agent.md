---
adr: 058
title: Inline Reviewer Replaces Async impl-review Agent
status: Accepted
date: 2026-04-06
---

# ADR-058 — Inline Reviewer Replaces Async impl-review Agent

## Status

Accepted

## Context

ADR-014 introduced async impl-review: spawn background agent after REFACTOR,
poll at next iteration start. This created a deferred polling loop, reviewer_status
state tracking, and background wait before final commit.

## Decision

Replace async Agent spawn with inline Skill() invocation inside `/implement`.
Review is gated on HIGH risk tasks only. Auto-fix protocol: issues found → fix
inline → test → pass/continue or fail after 1 retry → interrupt user.

## Consequences

**Positive:** Eliminates background wait, polling state, and context overhead from
Agent spawn. Faster per-task cycle. Simpler implement.md with no async coordination.

**Negative:** Reviews no longer run in parallel with the next task. Acceptable
because haiku/low reviews are fast (~seconds).

**Neutral:** ADR-014 is now superseded for impl-review behavior.

## Alternatives

Keep async pattern but reduce scope to only final review — rejected because polling
complexity outweighed benefit once review moved to haiku/low.
