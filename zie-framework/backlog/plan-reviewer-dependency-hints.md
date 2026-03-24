# plan-reviewer Dependency Hints

## Problem

`plan-reviewer` checks plan completeness and TDD structure but never
evaluates task parallelism. Tasks without `<!-- depends_on: -->` annotations
run sequentially in `/zie-implement` even when they are fully independent.
Most plans have no annotations because the author doesn't think to add them.

## Motivation

Parallelism in `/zie-implement` is gated entirely on `depends_on` comments.
If the plan-reviewer identifies independent tasks and suggests annotations,
the developer gets the speed benefit without needing to reason about
dependencies manually. One reviewer check unlocks parallel execution for
every feature that uses it.

## Rough Scope

- Add to plan-reviewer Phase 2: scan tasks for shared file dependencies —
  tasks that modify no common files and have no data dependency are
  independent
- If independent tasks found with no `depends_on` annotation → flag as
  suggestion (not error): "Tasks N and M appear independent — consider
  adding `<!-- depends_on: -->` to enable parallel execution"
- Out of scope: automatically adding annotations; changing how depends_on
  works in implement
