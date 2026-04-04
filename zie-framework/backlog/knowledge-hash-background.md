# Move knowledge-hash Drift Check Off SessionStart Critical Path

## Problem

`session-resume.py:143-155` runs `subprocess.run([sys.executable, knowledge-hash.py, "--check", ...], timeout=10)` synchronously during SessionStart. This blocks Claude from becoming interactive until the drift check completes — adding wall-clock latency proportional to codebase size on every session start.

## Motivation

The drift warning is purely informational — it does not gate any operation and Claude can proceed without it. Background execution is already the established pattern in this codebase (`wip-checkpoint.py` and `session-cleanup.py` both use `background: true`). Deferring to background or to the first `UserPromptSubmit` eliminates the startup latency entirely.

## Rough Scope

- Move the `subprocess.run` drift check to a separate background hook, OR
- Run it via `subprocess.Popen` (non-blocking) and discard the result if not needed synchronously
- Alternatively, register a separate `UserPromptSubmit` hook for first-prompt-only drift check
- The drift warning output can still be printed — just not on the critical SessionStart path
