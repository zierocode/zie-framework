---
tags: [bug]
---

# Fix Pending Learn Double Write

## Problem

`session-stop.py` writes `pending_learn.txt` to `zie-framework/pending_learn.txt` (project-local path) while `session-learn.py` writes to `$CLAUDE_PLUGIN_DATA/pending_learn.txt` (plugin data path). But `session-resume.py` only reads from the project-local path, making the plugin-data copy orphaned — never consumed.

## Motivation

One write is completely wasted. Worse, if the paths diverge in content, the auto-learn feature could read stale or incorrect patterns.

## Rough Scope

**In:**
- Remove the duplicate write in `session-learn.py` (keep only the project-local path that session-resume reads)
- Or: consolidate to a single canonical path and update session-resume reader

**Out:**
- Changing the auto-learn feature behavior