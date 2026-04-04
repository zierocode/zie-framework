---
slug: audit-stopfailure-stderr
status: draft
date: 2026-04-01
---
# Spec: Surface All Non-Trivial StopFailure Error Types to Stderr

## Problem

`stopfailure-log.py` only prints a stderr message for `rate_limit` and
`billing_error`. All other `error_type` values — `context_limit`, `api_error`,
and `unknown` — are written silently to the `/tmp` log only. The user receives
no visible feedback at session stop.

`context_limit` is the most impactful gap: a user whose session ends due to
context limit has an immediate, actionable next step (`/compact` or start a new
session), but currently sees nothing at the terminal.

`api_error` and `unknown` also warrant a visible message — the user should
know something went wrong, even if the remedy is not as clear-cut.

## Proposed Solution

Extend the existing stderr branch in `stopfailure-log.py` to cover
`context_limit`, `api_error`, and `unknown` with per-type messages that match
the existing format:

```
[zie-framework] Session stopped: <human-readable message>
```

Proposed messages:

| `error_type`    | Stderr message                                                                      |
|-----------------|-------------------------------------------------------------------------------------|
| `rate_limit`    | `Session stopped: rate_limit. Wait before resuming.` (existing — unchanged)        |
| `billing_error` | `Session stopped: billing_error. Wait before resuming.` (existing — unchanged)     |
| `context_limit` | `Session stopped: context limit reached. Run /compact or start a new session.`     |
| `api_error`     | `Session stopped: api_error. Check API status or retry.`                           |
| `unknown`       | `Session stopped: unknown error. Check /tmp log for details.`                      |

The stderr print for each type is an inner-tier operation — it lives inside the
existing outer `try` block. If printing fails, the outer `except` catches it
and the hook still exits 0.

No changes to the `/tmp` log format, the outer guard, or the early-exit check.

## Acceptance Criteria

- [ ] AC1: When `error_type == "context_limit"`, `stopfailure-log.py` prints
  `[zie-framework] Session stopped: context limit reached. Run /compact or start a new session.`
  to stderr.
- [ ] AC2: When `error_type == "api_error"`, the hook prints
  `[zie-framework] Session stopped: api_error. Check API status or retry.`
  to stderr.
- [ ] AC3: When `error_type == "unknown"`, the hook prints
  `[zie-framework] Session stopped: unknown error. Check /tmp log for details.`
  to stderr.
- [ ] AC4: Existing `rate_limit` and `billing_error` messages are unchanged.
- [ ] AC5: The `/tmp` log entry is still written for all `error_type` values
  (no regression).
- [ ] AC6: The stderr prints are inner-tier operations — a failure to print
  does not cause the hook to exit non-zero or raise an unhandled exception.
- [ ] AC7: Unit tests cover each new `error_type` branch and assert the correct
  stderr output.

## Out of Scope

- Changing the `/tmp` log format or adding structured fields.
- Supporting additional `error_type` values not present in the Claude API today.
- Localisation or i18n of the messages.
- Writing the messages anywhere other than stderr (e.g. a notification system).
