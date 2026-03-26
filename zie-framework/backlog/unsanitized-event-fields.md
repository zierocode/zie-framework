# security: sanitize and bound event-controlled fields in logs

## Problem

Multiple hooks write unsanitized event-controlled values directly to log files
and Claude context:

- `stopfailure-log.py:16-28`: error_type, error_details written verbatim
- `notification-log.py:64-77`: message field stored in JSONL and emitted back
  via additionalContext

No length caps or character sanitization. Malicious events could:
- Inject newlines to forge log entries
- Supply unbounded values to fill disk
- Inject context into Claude's prompt via additionalContext

## Motivation

- **Severity**: Medium
- **Source**: /zie-audit 2026-03-26 finding #15

## Scope

- Add length cap (e.g., 10KB) to event fields before storage
- Strip/escape newlines in single-line log formats
- Apply to all hooks that write event data to files
