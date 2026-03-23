# Backlog: StopFailure Hook — API Error Logging + Notification

**Problem:**
When Claude Code's API fails (rate limit, billing error, server error), the
session silently stops. There's no logging, no notification, and no context
about what was in progress when the failure occurred.

**Motivation:**
`StopFailure` fires on API errors with `error` type and `last_assistant_message`.
Logging this with the current SDLC state provides an audit trail. For billing
or rate limit errors, a desktop notification helps the user know to wait before
resuming.

**Rough scope:**
- New hook: `hooks/stopfailure-log.py` (StopFailure event, async: true)
- Append to `project_tmp_path("failure-log")`: timestamp, error type, ROADMAP
  Now lane, error_details if present
- For `rate_limit` or `billing_error`: write to stderr (shown to user as
  notification)
- For other errors: silent log only
- Register with `async: true` (logging must not block or fail)
- Tests: log written on all error types, rate_limit stderr output, async safe
