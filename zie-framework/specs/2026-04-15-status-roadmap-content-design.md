---
date: 2026-04-15
status: approved
slug: status-roadmap-content
---

# Status Roadmap Content Summary

## Problem

`/status` reads ROADMAP lanes (Now/Next/Done) but only shows item counts and slugs. Users must open each backlog, spec, or plan file to understand what's actually in the pipeline.

## Solution

Extend `/status` step 7 output: for each item in Now and Ready lanes, read the corresponding `backlog/<slug>.md` and extract the first 1-2 lines of the `## Problem` section. Also show spec/plan existence as a checklist (spec ✓/—, plan ✓/—). Reuse `parse_roadmap_section` and `parse_roadmap_section_content` from `utils_roadmap.py` to get lane items, then read backlog files for excerpts.

## Rough Scope

**In:** Read `backlog/<slug>.md` Problem excerpt (first ~120 chars) per Now/Ready item; show spec/plan file-existence status; keep output under 5 extra lines.

**Out:** Full file contents in status; changes to ROADMAP format; changes to `utils_roadmap.py`.

## Files Changed

- `commands/status.md` — add content-summary step after step 7, before step 7.5