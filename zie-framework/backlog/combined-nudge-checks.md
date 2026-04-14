---
tags: [chore]
---

# Combined Nudge Checks — single git log pass

## Problem

3 nudge conditions in stop-guard.py lines 80-120 (status, nudges, pipeline) each run git log --oneline. 3 git log calls per Stop; 30min TTL but still 3× work.

## Motivation

Single git log pass; parse once; distribute to all nudge checks. ~100 tokens saved per Stop.

## Rough Scope

**In:**
- `hooks/stop-handler.py` — combined nudge checks
- Single git log call, parse once

**Out:**
- Nudge logic (unchanged)

<!-- priority: LOW -->
<!-- depends_on: stop-handler-merge -->
