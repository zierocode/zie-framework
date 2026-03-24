# Implement Loop — Inline Guidance + Parallel Tasks by Default

## Problem

`/zie-implement` invokes `Skill(zie-framework:tdd-loop)` and
`Skill(zie-framework:test-pyramid)` for every task. Both are guidance-only
skills — they output the same RED/GREEN/REFACTOR steps and "unit test for this
type of code" answer on nearly every invocation. Two extra model calls per
task add up fast on a multi-task plan.

Separately, independent tasks only parallelize when the plan author explicitly
annotates `<!-- depends_on: -->`. Without annotations, all tasks run
sequentially even when they could safely parallelize.

## Motivation

Removing per-task skill invocations for pure guidance and enabling parallel
execution by default are the two structural changes with the highest speed
impact in the implement loop.

## Rough Scope

- Embed tdd-loop guidance (RED/GREEN/REFACTOR summary) as inline text printed
  once at the start of the implement session — not invoked per task
- Embed test-pyramid decision inline as a simple rule: "unit for isolated
  logic, integration for cross-module, e2e for UI flows" — no per-task
  invocation
- Still invoke `Skill(zie-framework:tdd-loop)` when the plan has a
  `tdd: deep` hint or when a test fails unexpectedly (debug path)
- Parallelize tasks with no `depends_on` by default (current: requires explicit
  annotation). Tasks that share files or have sequential logic should annotate
  `<!-- depends_on: T1 -->`
- Out of scope: changing the TDD process itself; reviewer logic
