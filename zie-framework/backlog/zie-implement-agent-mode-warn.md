# zie-implement: Make Agent-Mode Check Warn-Only (Non-Blocking)

## Problem

`commands/zie-implement.md:17-19` emits an interactive prompt asking the user to confirm or cancel when not running in agent mode. This adds a round-trip pause and extra user interaction at the start of every common inline `/zie-implement` invocation. The user already issued the command — blocking them to confirm is friction without safety benefit.

## Motivation

One unnecessary interactive round-trip per non-agent-mode implementation run. Changing to a one-line warning (print and continue) preserves the informational value while eliminating the blocking confirmation and the associated turn cost.

## Rough Scope

- Replace the interactive yes/cancel prompt with a one-line warning message
- Continue execution immediately after the warning
- Update any tests that assert the interactive prompt behavior
