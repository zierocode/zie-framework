# Spec: safety_check_agent — Use Haiku for Binary ALLOW/BLOCK Decision

status: draft

## Problem

`safety_check_agent.py` spawns a Claude subprocess (inheriting the session model — currently Sonnet 4.6) to evaluate a 4-line ALLOW/BLOCK prompt on every Bash tool call when `safety_check_mode` is `agent` or `both`. Sonnet is dramatically over-spec for a single-word binary classification. A 20-Bash-call TDD session in agent mode burns 20 full Sonnet round-trips, each returning one word.

## Solution

Add `--model claude-haiku-4-5-20251001` to the `claude --print` subprocess call inside `invoke_subagent`. No config key is needed — Haiku is always the correct model for this use case (~80% cost reduction, same quality for ALLOW/BLOCK).

The change is one line in `hooks/safety_check_agent.py`:

```python
["claude", "--print", "--model", "claude-haiku-4-5-20251001", prompt],
```

## Acceptance Criteria

- [ ] AC1: `invoke_subagent` passes `--model claude-haiku-4-5-20251001` in the subprocess args list
- [ ] AC2: Existing injection-guard tests (`test_safety_check_agent_injection.py`) still pass unchanged
- [ ] AC3: New unit test asserts `--model` flag and model ID appear in the subprocess call args
- [ ] AC4: CLAUDE.md config table updated — note that Haiku is hardcoded (no config key)

## Out of Scope

- Making the model configurable (Haiku is always correct here)
- Changes to regex path, `_regex_evaluate`, or other hooks

## Open Questions

- None — model ID is pinned at `claude-haiku-4-5-20251001` per backlog spec.
