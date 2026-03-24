# Reviewer Shared Context Bundle

## Problem

All three reviewers (spec-reviewer, plan-reviewer, impl-reviewer) each
independently read `zie-framework/decisions/*.md` and
`zie-framework/project/context.md` from disk. In a typical spec → plan →
implement session, the same ADR files and context doc are read 3 times
with no changes between reads.

## Motivation

ADRs and context.md are static within a session — they don't change while
you're working on a feature. Re-reading them per reviewer is redundant I/O.
Passing a pre-loaded context bundle from the caller to each reviewer
eliminates duplicate reads and reduces reviewer startup time.

## Rough Scope

- In `/zie-plan` and `/zie-implement`: load ADRs + context.md once before
  the reviewer loop, pass contents as part of the reviewer invocation
  context rather than letting each reviewer re-read them
- Each reviewer still uses the same data — no behavioral change
- Fallback: if caller doesn't pass the bundle, reviewer reads from disk as
  today (backward compatible)
- Out of scope: caching across sessions; sharing context between different
  features
