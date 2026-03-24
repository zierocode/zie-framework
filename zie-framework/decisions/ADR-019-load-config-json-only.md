# ADR-019: load_config() Parses JSON Exclusively

Date: 2026-03-25
Status: Accepted

## Context

`zie-framework/.config` has always been a JSON file, but the previous
`load_config()` implementation used a KEY=VALUE INI-style parser. The function
appeared to work (returned an empty dict on parse failure) but silently dropped
all config values — including `safety_check_mode`, which meant the agent-based
safety check was never activated even when explicitly configured.

## Decision

`load_config()` calls `json.loads()` directly on the file contents. Any parse
error raises an exception caught by the outer `except Exception: return {}`.
No fallback INI parsing; the `.config` format is JSON, period.

## Consequences

**Positive:** Config values are now actually applied. The silent failure mode
is eliminated — a corrupt `.config` still returns `{}` safely, but a valid
JSON `.config` is now correctly read.
**Negative:** Projects that somehow had a non-JSON `.config` will silently get
`{}` instead of partially parsed values (same as before, but for different
reasons).
**Neutral:** `.config` format was already documented as JSON in templates; this
aligns the implementation with the spec.
