# Session-Resume Hook Output Compression

## Problem

The `session-resume.py` hook fires on every SessionStart and prints a full
project state snapshot — project name, version, brain status, knowledge
status, active feature, ROADMAP summary, test health, and next suggested
command. This output enters the context window immediately on session start,
consuming tokens before any user prompt is even processed.

## Motivation

The session-resume output is the first thing that lands in every session's
context. Compressing it to 3–4 lines reduces the baseline context cost for
every session. The essential information (what project, what's active, what
to do next) fits in one line. The rest is available on demand via
`/zie-status`.

## Rough Scope

- Reduce session-resume hook output to maximum 4 lines:
  `[zie-framework] <project> (<type>) v<version>`
  `  Active: <feature name or "No active feature">`
  `  Brain: <enabled|disabled>`
  `  → Run /zie-status for full state`
- Full detail remains available via `/zie-status` (unchanged)
- Out of scope: changing what `/zie-status` shows; changing other hooks
