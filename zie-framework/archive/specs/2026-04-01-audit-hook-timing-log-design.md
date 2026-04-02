---
slug: audit-hook-timing-log
status: approved
date: 2026-04-01
---
# Spec: Hook Execution Timing Log

## Problem

Hook execution time, failure rates, and invocation frequency are entirely
invisible. The `[zie-framework] hook-name: error` stderr pattern alerts on
individual failures but provides no aggregate signal. There is no way to
identify which hooks are contributing to session latency or firing most often.

## Proposed Solution

Extend `utils.py` with a `log_hook_timing(hook_name, duration_ms, exit_code)`
utility that appends a structured JSON record to the same session-scoped tmp
file used by `notification-log.py` (pattern: `project_tmp_path("hook-timing-log",
project)`).

Each hook that opts in wraps its `__main__` block with `time.monotonic()` calls
and writes one timing record per invocation:

```json
{"event": "hook_timing", "hook": "auto-test", "duration_ms": 312, "exit_code": 0}
```

The write is an inner-tier operation — it is wrapped in `except Exception as e:
print(...)` so a logging failure never blocks Claude.

**Phase 1 hooks** (highest value, implemented first):
- `auto-test.py`
- `safety-check-agent.py` (or `safety_check_agent.py`)
- `intent-sdlc.py`

**Log location**: `project_tmp_path("hook-timing-log", project)` — newline-delimited
JSON, same format as the permission-log. Cleared by `session-cleanup.py` on Stop.

**New util signature**:
```python
def log_hook_timing(hook_name: str, duration_ms: int, exit_code: int = 0) -> None:
    """Append a timing record to the session-scoped hook timing log.

    Inner-tier: errors are logged to stderr; never raises.
    """
```

`project` is resolved inside the util via `safe_project_name(get_cwd().name)`.

## Acceptance Criteria

- [ ] AC1: `utils.py` exports `log_hook_timing(hook_name, duration_ms, exit_code=0)` that appends `{"event": "hook_timing", "hook": ..., "duration_ms": ..., "exit_code": ...}` to `project_tmp_path("hook-timing-log", project)`.
- [ ] AC2: `log_hook_timing` is inner-tier: any exception is caught and printed to stderr; the function never raises.
- [ ] AC3: `auto-test.py` measures wall time with `time.monotonic()` around its outer guard + inner block and calls `log_hook_timing` before exit.
- [ ] AC4: `safety-check-agent.py` (or equivalent safety check hook) records timing the same way.
- [ ] AC5: `intent-sdlc.py` records timing the same way.
- [ ] AC6: The timing log file format is newline-delimited JSON, readable by `_read_records` (existing pattern).
- [ ] AC7: Hooks that do not opt in are unaffected — no API changes to existing hook signatures.
- [ ] AC8: Unit tests cover: (a) `log_hook_timing` happy path writes correct record, (b) `log_hook_timing` swallows exceptions without raising, (c) duration is a non-negative integer.

## Out of Scope

- Parsing or surfacing timing data in any command or UI (read-only log for now).
- Adding timing to every hook in the codebase (only Phase 1 three hooks).
- Persistent (cross-session) timing storage — tmp-only for v1.
- Alerting or thresholds based on timing values.
- `session-cleanup.py` changes — it already clears all `project_tmp_path` files.
