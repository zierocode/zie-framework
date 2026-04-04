---
status: Accepted
date: 2026-04-04
---

# ADR-043 — Consolidate input-sanitizer.py into safety-check.py

## Status
Accepted

## Context
PreToolUse fired two separate hooks (safety-check.py for BLOCKS/WARNS, input-sanitizer.py for metachar injection guard) on every Write|Edit|Bash event, spawning 3 subprocesses total (safety-check + input-sanitizer + safety_check_agent for Bash).

## Decision
Merge input-sanitizer.py logic into safety-check.py. safety-check.py now handles BLOCKS/WARNS patterns AND metachar injection guard for Bash commands, AND path traversal checks for Write/Edit. input-sanitizer.py is deleted. Subprocess count per Bash event reduced from 3 to 2.

## Consequences
**Positive:** Reduced subprocess spawn overhead, single code path for all pre-tool safety.
**Negative:** safety-check.py is now longer and handles two concerns.
**Neutral:** hooks.json simplified from two PreToolUse entries to one (plus the Bash-only safety_check_agent.py).

## Alternatives Considered
- Keep separate hooks but run input-sanitizer as an inline function call from safety-check, avoiding the subprocess spawn while preserving separation.
- Create a shared pre-tool-use library imported by both hooks, keeping concerns separate without duplicate subprocess overhead.
