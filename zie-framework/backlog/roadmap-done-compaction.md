# ROADMAP Done Section Auto-Compaction

## Problem

`ROADMAP.md` Done section grows ~+2 entries per release with no cleanup. Currently
36 entries / 100 lines. In 6 months at current pace: ~150+ entries / 400+ lines.
While `/zie-retro` already reads only the last 20 lines (so context impact is
mitigated today), the file becomes unwieldy for manual review and the growing tail
means the guard could drift if the read-limit is ever removed or changed.

## Motivation

Self-managing state files are a core zie-framework principle. A ROADMAP that auto-
compacts keeps the working file readable and consistent, even as the project ages.

## Rough Scope

- Add compaction step to `/zie-retro`: after updating Done section, if entry count
  > 20 → compact entries older than 6 months into a single dated summary line:
  `- [archive] v1.0–v1.5 (2026-03 to 2026-09): 42 features shipped — see zie-framework/archive/`
- Summary line replaces the old entries in-place; detail lives in `archive/`
- Keep the most recent 20 entries intact (always full detail for recent work)
- Tests: compaction triggers at >20 entries, summary line format, idempotent
