# stopfailure-log.py only surfaces 2 error types to stderr

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`stopfailure-log.py` surfaces only `rate_limit` and `billing_error` to stderr
with a visible user message. All other `error_type` values (`context_limit`,
`api_error`, `unknown`, etc.) are written silently to `/tmp` log only.

A user hitting a context limit would see no feedback at session stop — just
silence.

## Motivation

Surface all non-trivial StopFailure error types to stderr with a concise
one-line message. `context_limit` in particular is actionable: user should
know to use `/compact` or start a new session.
