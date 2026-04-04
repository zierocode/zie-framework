# Spec: intent-sdlc — Gate ROADMAP Read for Non-Now-Dependent Intents

status: draft

## Problem

In `hooks/intent-sdlc.py`, `read_roadmap_cached()` and `parse_roadmap_section_content()` fire unconditionally after any SDLC keyword match — even for intents like `backlog`, `spec`, `fix`, `release`, `retro`, `sprint`, and `init` that do not consume Now-lane data in any meaningful way.

The cache TTL is 30 seconds so re-reads within the window are cheap, but `parse_roadmap_section_content()` (a string-scan over the full ROADMAP) still executes on every matched prompt regardless of intent. Over a long session this is dead work for the majority of non-Now intents.

The ROADMAP read and Now-lane parse are only meaningfully consumed by three intents:

| Intent | Why it needs Now-lane |
| --- | --- |
| `implement` | `_check_pipeline_preconditions` checks Now for open items |
| `plan` | `_check_pipeline_preconditions` checks Next/Ready slugs |
| `status` | `_positional_guidance` and the task/stage status line |

For all other intents the Now-lane result only populates the trailing `task:... | stage:... | next:... | tests:...` fragment. Emitting `task:none | stage:idle` for non-Now intents is semantically correct (the user asked about backlog/spec/retro — not about what is running now) and eliminates the unnecessary parse.

## Solution

Gate `read_roadmap_cached()` and all downstream Now-lane work behind the detected intent:

```python
NOW_DEPENDENT_INTENTS = frozenset({"plan", "implement", "status"})

roadmap_content = ""
now_items = []
if best in NOW_DEPENDENT_INTENTS or intent_cmd is None:
    roadmap_content = read_roadmap_cached(roadmap_path, session_id)
    now_items = parse_roadmap_section_content(roadmap_content, "now")
```

`intent_cmd is None` covers the no-dominant-intent case where `_positional_guidance` fires (it needs ROADMAP).

For all other intents (`backlog`, `spec`, `fix`, `release`, `retro`, `sprint`, `init`), skip the read entirely. `active_task` defaults to `"none"` and `stage` to `"idle"`, which is the existing fallback already present in the hook.

`_check_pipeline_preconditions` and `_positional_guidance` already only fire for `plan`/`implement` and `status`/no-intent respectively — their existing guards remain unchanged.

## Acceptance Criteria

1. When intent is `backlog`, `spec`, `fix`, `release`, `retro`, `sprint`, or `init`, `read_roadmap_cached()` is NOT called (verified via monkeypatching or a counter).
2. When intent is `plan`, `implement`, or `status`, `read_roadmap_cached()` IS called and Now-lane data appears in output.
3. When no dominant intent is detected (`intent_cmd is None`), `read_roadmap_cached()` IS called so `_positional_guidance` can run.
4. Pipeline gate (`⛔`) still fires correctly for `plan` (no approved spec) and `implement` (no Now item) — no regression.
5. Positional guidance still fires for `status` intent and no-dominant-intent prompts — no regression.
6. Existing test suite passes without modification (behaviour change is not observable in current tests since they do not assert ROADMAP is read for non-Now intents).
7. New tests added for non-Now intents confirming: output is produced (no silent exit), `⛔` is absent, `task:none` appears in context.

## Out of Scope

- Changing the cache TTL or cache key strategy.
- Gating `_check_pipeline_preconditions` (already gated at line 315).
- Altering the output format of the `task/stage/next/tests` status line.
- Changing behaviour for `plan` or `implement` intents in any way.
