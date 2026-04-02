# ADR-038: Hook Timing Instrumentation via Session Log

## Status
Accepted

## Context
Hook execution time was invisible — no way to diagnose which hooks were slowing session startup or PostToolUse latency. Multiple hooks (session-resume, auto-test) ran subprocesses with unknown duration.

## Decision
Add `log_hook_timing(hook_name, duration_ms, exit_code, session_id)` utility to `hooks/utils.py`. Each instrumented hook appends a JSON line to `/tmp/zie-{safe_session_id}/timing.log` on every invocation. Session ID is sanitized via `re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)`. The function is a no-op when session_id is empty or None, and never raises.

## Consequences
**Positive:** Hook latency becomes observable without external tooling. Timing data survives session for post-hoc analysis.
**Negative:** Adds one file write per hook invocation per session (negligible I/O).
**Neutral:** Only session-resume and auto-test instrumented initially; other hooks can be added incrementally.

## Alternatives
Considered: stderr timing output (too noisy), prometheus-style metrics (overkill for solo dev), no-op (blocked diagnosis). Session log chosen for low noise and persistence.
