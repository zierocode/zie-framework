# safety_check_agent: Use Haiku for Binary ALLOW/BLOCK Decision

## Problem

`safety_check_agent.py` spawns a full Claude subprocess (inheriting the session model — currently Sonnet 4.6) to evaluate a 4-line ALLOW/BLOCK prompt on every Bash tool call when `safety_check_mode` is `agent` or `both`. Sonnet is dramatically over-spec for binary classification.

## Motivation

Adding `--model claude-haiku-4-5-20251001` to the `invoke_subagent` subprocess call cuts per-call cost by ~80%. A 20-Bash-call TDD session in agent mode currently uses 20 full Sonnet round-trips for safety screening — each returning a single word. Haiku handles this perfectly.

## Rough Scope

- Add `--model claude-haiku-4-5-20251001` to the `claude --print` call in `invoke_subagent` (`safety_check_agent.py`)
- Update tests to assert the `--model` flag is present in the subprocess args
- Document in CLAUDE.md config table (no config key needed — Haiku is always correct here)
