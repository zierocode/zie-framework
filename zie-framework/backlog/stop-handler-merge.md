---
tags: [chore]
---

# Stop Handler Merge — consolidate 3 hooks → 1

## Problem

3 separate Stop hooks fire sequentially: stop-guard.py, stop-pipeline-guard.py, compact-hint.py. Each runs git status --short; nudge checks run with 30min TTL independently. 3 git status calls per Stop; redundant condition checks; 3× log writes.

## Motivation

Single stop-handler.py with unified logic: git status once, nudge checks combined, single log entry. ~600 tokens saved per Stop event.

## Rough Scope

**In:**
- `hooks/stop-handler.py` (new) — unified Stop handler
- Merge: stop-guard.py, stop-pipeline-guard.py, compact-hint.py logic
- Preserve all nudges

**Out:**
- Delete old 3 hook files after merge

<!-- priority: MEDIUM -->
<!-- depends_on: none -->
