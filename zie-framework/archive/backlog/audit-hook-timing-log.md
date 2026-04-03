# Hook timing log — structured execution timing per hook invocation

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

Hook execution time, failure rates, and which hooks fire most often are
entirely invisible. The `[zie-framework] hook-name: error` stderr convention
is good for alerting but provides no aggregate signal. There is no way to
identify which hooks are contributing to session latency.

## Motivation

`notification-log.py` already writes session-scoped logs — natural extension
point. Append a structured timing entry (hook name, duration ms, exit code)
to the session log on each hook completion. This costs ~5 lines per hook and
enables retrospective analysis (e.g., "auto-test is slowest in the pipeline").
