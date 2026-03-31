# ADR-034 — Phase-Parallel Sprint Orchestration

**Status:** Accepted
**Date:** 2026-04-01

## Context
Sequential pipeline execution (each backlog item goes spec→plan→implement→release→retro independently) creates O(N) overhead: N releases, N retros, ~25N context loads, N test gates. With a backlog of 5+ items, this becomes untenable.

## Decision
Implement /zie-sprint as a phase-parallel orchestrator: group all items through each pipeline phase together (spec/plan run in parallel per item, implement runs sequential WIP=1, then single batch release + single retro). This reduces N releases to 1, N retros to 1, context loads from ~25N to ~1.

## Consequences
**Positive:** Dramatically reduces ceremony overhead for batch sprints. Single release tag covers all shipped items. Single retro synthesizes all learnings.
**Negative:** Requires careful dependency detection to serialize items that depend on each other. Rollback granularity is per-sprint not per-item.
**Neutral:** Implementation stays as Markdown command, not Python hook.

## Alternatives
- Sequential per-item pipeline: O(N) overhead, already the default
- Manual batching by user: requires human judgment on each item
