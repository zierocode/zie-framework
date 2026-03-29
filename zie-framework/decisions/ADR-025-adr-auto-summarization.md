# ADR-025: ADR Auto-Summarization via /zie-retro

Date: 2026-03-30
Status: Accepted

## Context

Reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) load all
`decisions/*.md` on every invocation. At 24 ADRs / ~914 lines today and
growing ~1 ADR per release, the full ADR set will exceed practical context limits.

## Decision

When `/zie-retro` counts more than 30 individual ADR files, it generates
`decisions/ADR-000-summary.md` — a Markdown table compressing the oldest ADRs
(all except the 10 most-recent) into one row each — then deletes those individual
files. Reviewer skills load `ADR-000-summary.md` first when it exists, then
the remaining individual files.

## Consequences

**Positive:**

- Reviewer context window for ADRs stays bounded at ~10 full ADRs + 1 summary table.
- Compressed ADRs are recoverable from git history.
- Threshold constants (30/10) are fixed in code; no config knob (YAGNI).

**Negative:**

- `ADR-000-summary.md` is a generated artefact — not a primary source.
- Detail of compressed ADRs is reduced to one sentence per ADR.
