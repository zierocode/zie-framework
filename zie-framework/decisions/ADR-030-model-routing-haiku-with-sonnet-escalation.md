# ADR-030: Model Routing — Haiku Default with Sonnet Escalation for Judgment Steps

Date: 2026-03-30
Status: Accepted

## Context

zie-release and impl-reviewer execute many deterministic steps (file reads, version bumps, structured outputs) that do not require Sonnet-level reasoning. Running every step on Sonnet wastes cost with no quality benefit.

## Decision

Haiku is the default model for zie-release and impl-reviewer. Steps that require judgment or nuanced evaluation are annotated with `<!-- model: sonnet -->` as an inline signal to use Sonnet for that step only.

## Consequences

**Positive:** Lower token cost per release and review run; annotations serve as living documentation of which steps require reasoning.
**Negative:** Haiku may underperform on edge-case judgment if an unannotated step is more complex than expected.
**Neutral:** Model routing is annotation-driven, not automatic; maintainers must keep annotations accurate as steps evolve.
