# ADR Auto-Summarization — Context Cap for decisions/

## Problem

`spec-reviewer`, `plan-reviewer`, and `impl-reviewer` all call `read all decisions/*.md`
on every invocation. Currently 24 ADRs / 914 lines — growing ~+1 ADR (~38 lines) per
release. At 50 ADRs the three reviewers collectively load ~6,000+ lines of ADR content
per review session, compounding with every sprint.

## Motivation

ADRs must stay readable for reviewers (they exist to enforce architectural consistency),
but loading the full set indefinitely is wasteful. A summary ADR approach lets reviewers
load one compact reference for old decisions and full detail only for recent ones.

Automating this in `/zie-retro` means it happens naturally at the right time — right
after a release when new ADRs are written — with no manual intervention.

## Rough Scope

- Add ADR count check to `/zie-retro`: when `decisions/*.md` count > 30, auto-generate
  `ADR-000-summary.md` that compresses the oldest N ADRs into a table (ADR#, title,
  decision-in-one-line), then removes those files from `decisions/`
- Update reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer): load
  `ADR-000-summary.md` first (if exists), then full files for ADRs > summary cutoff
- Add `make adr-count` helper to surface current count
- Tests: summary generation, reviewer fallback when summary missing, idempotent re-run
