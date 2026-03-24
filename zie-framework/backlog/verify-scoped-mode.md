# verify Skill Scoped Mode

## Problem

`/zie-fix` calls `Skill(zie-framework:verify)` with "scope = tests only"
but the verify skill has no scope parameter — it runs all 5 checks
(tests, regressions, TODOs, code review, docs sync) regardless. Bug fixes
don't need docs sync or full code review, but they get it anyway.

## Motivation

A bug fix verify should confirm: tests pass, no regressions, no secrets.
It should not check docs sync or run a full code review — those belong to
the feature implementation path. The mismatch between what `/zie-fix`
intends and what the skill does is a latent bug that wastes time on every
bug fix.

## Rough Scope

- Add a `scope` parameter to the verify skill: `full` (default) or
  `tests-only`
- `tests-only`: run checks 1 (tests), 2 (no regressions), and partial 4
  (secrets only) — skip docs sync and full code review
- Update `/zie-fix` to pass `scope=tests-only` explicitly
- Out of scope: changing what "full" scope checks; adding other scope modes
