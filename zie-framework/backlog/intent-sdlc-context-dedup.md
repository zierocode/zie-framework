---
tags: [chore]
---

# intent-sdlc: Deduplicate Same-Context Injection Per Session

## Problem

`hooks/intent-sdlc.py` fires on every `UserPromptSubmit` event. When it detects
an SDLC-intent message it emits `additionalContext` (~150-200 tokens) with the
current intent suggestion and SDLC stage. During focused coding sessions where
many consecutive messages share the same intent and the SDLC stage hasn't changed,
the same context is re-injected redundantly on every turn.

## Motivation

Adding a session-level "last emitted context" cache (keyed on `session_id`) lets
the hook skip injection when the output would be identical to the previous emission
within the same session. The ROADMAP is already cached with a 30s TTL via
`read_roadmap_cached`; adding a last-output cache eliminates the token cost of
repeated identical injections during multi-turn focused work.

## Rough Scope

- Add `_last_context_cache: dict[str, str]` at module level in `intent-sdlc.py`
- Before emitting `additionalContext`: compute a cache key from
  `(session_id, intent_cmd, stage, active_task[:40])` — if matches last emitted
  for this session → `sys.exit(0)` (no re-injection)
- After emitting: update cache entry
- Cache is in-process only (no disk writes) — resets on hook process restart
- Tests: verify hook exits 0 without output when context unchanged
