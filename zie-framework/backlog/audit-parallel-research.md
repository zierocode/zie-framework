# /zie-audit Parallel External Research

## Problem

Phase 3 of `/zie-audit` runs up to 15 WebSearch queries sequentially.
Each query is fully independent — none depends on a prior result — but
they execute one after another, adding 30-45 seconds of pure latency to
every audit run.

## Motivation

All 15 queries are constructed upfront from `research_profile` before any
search runs. There is no reason they need to be sequential. Parallelizing
them brings Phase 3 latency from ~45s down to ~5s (single longest query),
which meaningfully reduces the 3-8 minute total audit time.

## Rough Scope

- In Phase 3: construct all queries first, then dispatch all WebSearch
  calls in parallel rather than in a loop
- Collect results and synthesize into `external_standards_report` as before
- Any failed query still skips gracefully with "Research unavailable"
- Out of scope: changing the query construction logic; changing the cap of
  15 queries; WebFetch follow-up calls (these can remain sequential as
  they depend on search results)
