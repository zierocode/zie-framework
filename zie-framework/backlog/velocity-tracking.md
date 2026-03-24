# Velocity Tracking

## Problem

`/zie-status` shows current state but gives no sense of throughput — there is
no way to know how fast features are shipping or whether the workflow is
improving over time.

## Motivation

A solo developer needs a feedback loop on their own process. Seeing "last 3
releases took 2 days, 1 day, 3 days" surfaces bottlenecks and validates that
workflow changes are working. The data already exists in git tags — no extra
instrumentation needed.

## Rough Scope

- Parse git tags (semver) to derive release dates
- Compute days between releases for last N releases (default: 5)
- Display in `/zie-status` output — one line, no new files or commands
- Out of scope: per-stage timing, external dashboards, metrics storage
