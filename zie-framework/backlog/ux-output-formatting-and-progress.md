# UX Output Formatting and Progress Visibility

## Problem

zie-framework output is inconsistent across commands — some steps are verbose,
some silent, formatting varies between hooks and commands. For long-running tasks
like `/zie-sprint`, there's no way to know how far along the session is, what's
left, or how long it will take.

## Motivation

A sprint that runs for an hour should feel like a controlled process, not a black
box. Consistent, well-structured output reduces cognitive load and builds trust in
the framework. Progress visibility (steps done, steps left, ETA) lets the developer
stay informed without interrupting the workflow.

## Rough Scope

**In:**
- Standardized output format across all commands — consistent headers, step
  indicators, success/failure markers
- Unicode progress bars for multi-step operations: `████████░░ 8/10 steps (80%)`
- Step-by-step progress printing during sprint and implement (each phase announced
  before starting)
- ETA estimation using velocity data from git history (ties into
  smarter-framework-intelligence)
- Task list as live progress tracker during sprint — each phase as a TaskCreate,
  marked complete as it finishes
- Hook output formatting — consistent `[zie-framework]` prefix, structured
  key: value pairs instead of prose

**Out:** Graphical UI, real-time overwrite/streaming bars, external dashboard.
