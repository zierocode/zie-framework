---
date: 2026-04-15
status: approved
slug: intent-sdlc-lean
---

# Implementation Plan — intent-sdlc-lean

## Steps

1. **Add new-intent groups to INTENT_PATTERN** — add `new_sprint`, `new_fix`, `new_chore` named groups containing the patterns currently in `NEW_INTENT_REGEXES`. Remove overlap with existing groups (e.g., `\bimplement\b` is already in `implement` group — skip duplicate alternatives).

2. **Replace NEW_INTENT_REGEXES iteration** — delete `NEW_INTENT_REGEXES` dict and the `for` loop (lines 121–134, 393–415). After the single `INTENT_PATTERN.search()`, count how many of the new-intent groups matched. If ≥2 for any category, emit the hint and exit.

3. **Raise early-exit threshold** — change `len(message) < 15` to `len(message) < 50` on line 334. Keep the existing `len(message) < 3` and `len(message) > 500` guards unchanged.

4. **Clean up dead references** — remove `NEW_INTENT_HINTS` constant (lines 135–139) since the same strings are redefined inline at line 352. The inline version is the one actually used.

## Tests

- **Short message early exit**: messages under 50 chars without strong keywords → exit without output. Under 50 chars with a keyword like "implement" → still detected.
- **Combined new-intent scoring**: a message with ≥2 `new_sprint` group matches (e.g., "build this feature now") fires sprint hint. Only 1 match → no hint.
- **Existing intent detection**: all 14 original intents still match after refactor. Run existing test suite — no regressions.
- **Dedup still works**: identical context within session window is suppressed.

## Acceptance Criteria

- `NEW_INTENT_REGEXES` dict removed from `intent-sdlc.py`
- All regex matching done in a single `INTENT_PATTERN.search()` call
- Short-message threshold raised to 50 characters
- All existing `test_intent_sdlc.py` tests pass without modification
- No change to hook output format or behavior for existing intents