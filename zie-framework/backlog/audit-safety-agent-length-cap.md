# Add command length cap before subagent prompt construction in safety_check_agent

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`safety_check_agent.py:46–59` `invoke_subagent()` passes the raw shell command
string directly into a `claude --print` subprocess prompt without any size
limit. An extraordinarily long command could produce a very large prompt,
causing slow evaluation or unexpected token behavior.

In practice the regex pre-filter in `safety-check.py` runs first (in `"both"`
mode) and the default mode is `"regex"`, limiting exposure. But in `"agent"`
mode there is no guard.

## Motivation

Add a character length cap (e.g., 4096 chars) before constructing the subagent
prompt. Truncate with a visible marker so the agent knows the command was cut.
