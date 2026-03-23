# intent-detect.py recompiles all regex patterns on every invocation

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`intent-detect.py:80-83` reconstructs `COMPILED_PATTERNS` from scratch on every
`UserPromptSubmit` event. As a standalone script (not a daemon), there's no
in-memory cache between invocations. Each user message pays full compilation cost
for 96 patterns.

## Motivation

Move pattern compilation to module-level constants so Python caches them in
`.pyc`. Alternatively, pre-generate a compiled cache file. Reduces per-event
latency and eliminates the ReDoS accumulation window.
