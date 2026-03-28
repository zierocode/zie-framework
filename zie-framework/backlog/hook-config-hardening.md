# Hook Config Hardening — Configurable Timeouts, .config Validation, Bounded Auto-test

## Problem

Three related hook configuration gaps:

1. **Hardcoded timeouts:** `failure-context.py`, `safety_check_agent.py`, and
   `stop-guard.py` use hardcoded subprocess timeouts (5s, 30s, 5s respectively).
   In slow CI environments or on large repos, these cause spurious timeout failures.
   Cannot be tuned without editing source.

2. **No .config schema validation:** `load_config()` in utils.py returns empty dict
   on any parse failure and logs to stderr. Hooks then call `config.get("key")` with
   no guarantee the key exists. Silent config degradation — user doesn't know their
   config is being ignored.

3. **Unbounded auto-test execution:** `auto-test.py` runs `make test-unit` and waits
   up to `subprocess_timeout` seconds (default: whatever the OS gives). If tests hang
   (deadlock, waiting for port, etc.), the hook blocks Claude's next action for the
   full timeout. No max wall-clock guard.

## Motivation

Hooks must be predictable and configurable for enterprise deployments. Hardcoded
timeouts are a maintenance liability; .config validation prevents silent degradation;
bounded auto-test prevents the worst UX failure mode (session freeze during TDD).

## Rough Scope

**Configurable timeouts — add to .config schema:**
```json
{
  "subprocess_timeout_s": 5,
  "safety_agent_timeout_s": 30,
  "auto_test_max_wait_s": 15
}
```
- Update `load_config()` to return typed defaults for all timeout keys
- Update `failure-context.py`, `safety_check_agent.py`, `stop-guard.py` to read
  from config instead of hardcoded values

**.config schema validation:**
- Add `validate_config(config: dict) -> dict` to utils.py: fills missing keys with
  documented defaults, logs a single warning line if any key was defaulted
- Replace all `config.get("key", default)` call sites with validated config access
- Document schema in CLAUDE.md config table

**Bounded auto-test:**
- In `auto-test.py`: wrap `make test-unit` in a wall-clock timer (threading.Timer)
  set to `auto_test_max_wait_s` (default: 15s)
- On timeout: kill subprocess, print `[zie-framework] auto-test: timed out after 15s
  — tests may be hanging. Run make test-unit manually.`
- Exit 0 regardless (never block Claude)

**Tests:**
- load_config() fills defaults when keys missing
- validate_config() logs warning on incomplete config
- auto-test kills subprocess at wall-clock limit and exits 0
- timeout values read from config, not hardcoded
