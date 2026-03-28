# architecture: fix hook JSON output protocol inconsistencies

## Problem

Three distinct JSON shapes are used for `additionalContext` injection:

1. **Flat** (correct for UserPromptSubmit): `{"additionalContext": "..."}`
   — used by intent-detect, failure-context, config-drift, notification-log
2. **PostCompact nested**: `{"hookSpecificOutput": {"additionalContext": "..."}}`
   — used by auto-test.py:95, sdlc-compact.py:139
3. **Mixed sibling** (wrong): wraps hookSpecificOutput AND sibling additionalContext
   — used only by sdlc-context.py:97-100

`sdlc-context.py` emits the PostCompact protocol shape for a UserPromptSubmit
event — context may be dropped or double-wrapped by the runtime.

## Motivation

- **Severity**: High (sdlc-context wrong protocol), Medium (inconsistent shapes)
- **Source**: /zie-audit 2026-03-26 findings #13, #34
- Wrong protocol shape means SDLC context injection may silently fail

## Scope

- Fix sdlc-context.py to emit flat `{"additionalContext": "..."}`
- Consider adding a `emit_context(event_type, context)` helper to utils.py
- Update hooks.json `_hook_output_protocol` to document all event types (#52)
