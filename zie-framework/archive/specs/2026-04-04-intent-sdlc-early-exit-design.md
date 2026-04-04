---
id: intent-sdlc-early-exit
title: Intent SDLC — Length + Keyword Early-Exit Guard
status: draft
approved: false
created: 2026-04-04
author: zie
---

# Intent SDLC — Length + Keyword Early-Exit Guard

## Problem

`hooks/intent-sdlc.py` performs a `read_roadmap_cached()` call (disk I/O or
cache lookup) and all downstream SDLC logic for **every** user message that
passes the outer guard — including trivial messages like "ok", "yes", "thx",
"👍", or any free-form message that mentions no SDLC concept.

Two concrete waste paths:

1. **Very short messages** (< 15 chars after strip) — "ok", "sure", "go", etc.
   These can never contain meaningful SDLC intent and should never trigger SDLC
   work.
2. **No-keyword messages** — messages long enough to pass the length check but
   containing zero SDLC-related terms (e.g. "what's the weather like?", a
   pasted URL, a JSON blob). For these, matching against `COMPILED_PATTERNS`
   already yields zero hits; there is no reason to proceed to `read_roadmap_cached`.

### Current code path (inner block, line 269+)

```
read_event()  ← outer guard
 ↓ passes
[inner block]
  scores = {cat: count for COMPILED_PATTERNS matches}
  intent_cmd = SUGGESTIONS[best] if scores else None
  read_roadmap_cached(...)      ← always called regardless of scores
  ...pipeline gates, guidance, context build
```

The ROADMAP read is unconditional once the inner block starts.

## Proposed Solution — Option A: Length + Keyword Guard

Add two sequential early-exit checks at the **very top** of the inner block,
before `read_roadmap_cached()`:

### Gate 1 — Length guard

```python
if len(message.strip()) < 15:
    sys.exit(0)
```

Threshold of 15 characters was chosen because:
- The shortest meaningful SDLC phrase ("fix", "plan", "backlog") needs context
  to be actionable, and real actionable phrases ("there is a bug", "plan this
  feature") are at least 15 chars.
- All existing passing tests use messages longer than 15 chars.
- The existing outer guard already exits on `len < 3`; this raises the bar to 15.

### Gate 2 — Keyword guard

```python
has_sdlc_keyword = any(
    p.search(message)
    for compiled_pats in COMPILED_PATTERNS.values()
    for p in compiled_pats
)
if not has_sdlc_keyword:
    sys.exit(0)
```

Reuses the already-compiled `COMPILED_PATTERNS` dict (zero extra cost).
If no pattern matches across all categories, the message carries no SDLC
signal → skip ROADMAP read entirely.

### Placement

Both gates are inserted **immediately after the opening of the inner `try`
block**, before any other inner-block logic:

```python
try:
    session_id = event.get("session_id", "default")

    # ── Early-exit guards ──────────────────────────────────────────────────────
    if len(message.strip()) < 15:
        sys.exit(0)

    has_sdlc_keyword = any(
        p.search(message)
        for compiled_pats in COMPILED_PATTERNS.values()
        for p in compiled_pats
    )
    if not has_sdlc_keyword:
        sys.exit(0)

    # ── Intent detection (no ROADMAP needed) ──────────────────────────────────
    ...
```

`message` is already lowercased and stripped by the outer guard, so
`message.strip()` in Gate 1 is a no-op but kept for clarity.

## Acceptance Criteria

| # | AC | Verification |
|---|---|---|
| AC-1 | A message with `len(message.strip()) < 15` (after outer-guard lowering) produces no stdout and exits 0. | Unit test with "ok", "yes", "go", "thx 👍", "sure!" |
| AC-2 | A message ≥ 15 chars that matches no `COMPILED_PATTERNS` produces no stdout and exits 0. | Unit test with "what is the weather?", "https://example.com/some/path", a pasted JSON blob |
| AC-3 | A message ≥ 15 chars that matches at least one `COMPILED_PATTERNS` entry continues to `read_roadmap_cached` and produces normal additionalContext output. | Unit test with valid SDLC messages: "there is a bug in auth", "implement this feature now", "plan this backlog item" |
| AC-4 | All existing passing tests in `test_hooks_intent_sdlc.py` continue to pass unchanged. | `make test-fast` |
| AC-5 | The keyword guard reuses `COMPILED_PATTERNS` directly — no new regex compilation introduced. | Verified by `test_intent_sdlc_regex.py` (existing AST check) |
| AC-6 | Both gates live inside the inner `try` block, never in the outer guard. | Code review / grep |

## Out of Scope

- No change to the outer guard logic.
- No change to `COMPILED_PATTERNS`, `PATTERNS`, or any detection heuristics.
- No change to ROADMAP read, pipeline gates, or positional guidance logic.
- No new config keys.

## Test Plan

New test file: `tests/unit/test_intent_sdlc_early_exit.py`

### Class `TestLengthGate`

| Test | Input prompt | Expected |
|---|---|---|
| `test_empty_string_exits` | `""` (caught by outer guard, len < 3) | stdout == "" |
| `test_two_char_exits` | `"ok"` | stdout == "" |
| `test_14_char_exits` | `"implement this"` (14 chars) | stdout == "" |
| `test_15_char_passes` | `"implement this!"` (15 chars, has SDLC keyword) | stdout != "" |
| `test_borderline_with_spaces` | `"  ok  "` (strips to "ok", 2 chars) | stdout == "" |

### Class `TestKeywordGate`

| Test | Input prompt | Expected |
|---|---|---|
| `test_no_keyword_long_message_exits` | `"what is the weather today over there"` (36 chars, no SDLC keyword) | stdout == "" |
| `test_url_only_exits` | `"https://example.com/some/path/here"` | stdout == "" |
| `test_generic_question_exits` | `"can you explain how async works here"` | stdout == "" |
| `test_fix_keyword_passes` | `"there is a bug in the auth module"` | stdout != "" |
| `test_implement_keyword_passes` | `"let us implement this feature now"` | stdout != "" |
| `test_plan_keyword_passes` | `"we should plan this backlog item"` | stdout != "" |

### Regression

All tests in `TestIntentSdlcHappyPath`, `TestIntentSdlcEarlyExit`,
`TestIntentSdlcRoadmapCache`, `TestPipelineGates`, `TestPositionalGuidance`,
and `TestHelperFunctions` must continue to pass.

## Implementation Notes

- Both gates must call `sys.exit(0)` — not `return` — because the inner block
  is not inside a function; it is top-level script flow.
- The `has_sdlc_keyword` variable name is local to the inner block; no module-level
  symbol is added.
- This change is a pure performance optimisation — no observable behaviour change
  for SDLC messages.
