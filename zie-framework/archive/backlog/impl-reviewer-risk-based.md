# impl-reviewer Risk-Based Invocation

## Problem

`/zie-implement` invokes `impl-reviewer` after every task regardless of
complexity. A plan with 8 tasks can trigger 24+ model calls from reviewer
iterations alone. Simple tasks — adding a test, updating docs, renaming a
variable — get the same review overhead as new functions or security-sensitive
changes.

## Motivation

Most review time is spent on low-risk tasks that rarely have issues. Routing
only risky tasks through the reviewer preserves quality where it matters while
eliminating most of the per-task latency.

## Rough Scope

- Define a risk classification inline in `/zie-implement`:
  - **Always review**: new function/class, changed behavior, external API call,
    security-sensitive code (auth, file I/O, subprocess), any task flagged
    `<!-- review: required -->`
  - **Skip reviewer**: add/edit test only, docs/config change, rename/reformat,
    minor addition (new field, extend existing list)
- Classify based on task description + files changed after GREEN phase
- Tasks that skip reviewer still run `make test-unit` — no quality gate removed
- Out of scope: changing the reviewer logic itself; model selection (see
  model-haiku-fast-skills)
