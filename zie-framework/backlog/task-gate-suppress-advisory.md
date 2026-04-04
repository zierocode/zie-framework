# task-completed-gate: Suppress stdout Advisory Message When Gate Is Skipped

## Problem

`task-completed-gate.py:119` prints `"[zie-framework] task-completed-gate: advisory task — gate skipped"` to stdout and exits when the task title doesn't match `implement` or `fix`. This string is injected as context into the conversation on every non-implement task completion. A hook that does nothing should be silent.

## Motivation

Every `TaskCompleted` event for planning tasks, status checks, or backlog additions injects this advisory noise into the context window. Removing the print makes the hook silent on skip — consistent with how other hooks handle early exits.

## Rough Scope

- Remove or comment out the stdout print at `task-completed-gate.py:119`
- Optionally redirect to stderr if debugging visibility is needed
- Update tests that assert this message appears
