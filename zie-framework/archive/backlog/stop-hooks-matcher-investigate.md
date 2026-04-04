# Investigate Stop Hook Matcher Support for Interactive-Session Gating

## Problem

All 4 Stop hooks in `hooks.json` (`stop-guard.py`, `compact-hint.py`, `session-learn.py`, `session-cleanup.py`) fire on every session stop with no matcher. This includes trivial stops, subagent stops, and error stops. The hooks.json comment block doesn't document whether Stop supports matchers.

## Motivation

If Claude Code supports matchers on Stop events, `stop-guard.py` (git subprocess) and `compact-hint.py` (context usage check) could be gated to interactive-only sessions, avoiding overhead on programmatic/subagent stops.

## Rough Scope

- Check Claude Code hooks reference for Stop event matcher support
- If supported: add appropriate matcher to stop-guard and compact-hint
- If not supported: document the platform constraint in hooks.json as a comment
- Low priority — hooks are already fast; gain is marginal
