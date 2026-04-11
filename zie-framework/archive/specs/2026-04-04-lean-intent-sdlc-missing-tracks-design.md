# lean-intent-sdlc-missing-tracks — Design Spec

**Problem:** `PATTERNS` in `intent-sdlc.py` covers 10 SDLC categories (init, backlog, spec, plan, implement, fix, release, retro, sprint, status) but omits the three off-pipeline tracks (`/hotfix`, `/chore`, `/spike`). Natural-language prompts like "emergency fix for prod" match `/fix` instead of `/hotfix`, and "let's explore this idea" matches nothing. Users are silently routed to wrong commands in urgent situations where the hotfix/fix distinction has concrete consequences (release-gate bypass vs. full pipeline).

**Approach:** Extend `PATTERNS` and `SUGGESTIONS` with three new categories — `hotfix`, `chore`, `spike` — using the keyword sets from the backlog item. Extend `no_track_msg` guard to also fire when `best` is one of these three new intents and no active Now-lane track exists, so the escape-hatch message stays coherent. No change to `STAGE_KEYWORDS` or `STAGE_COMMANDS` (those classify Now-lane task text, not user prompt intent). This is a surgical, additive change with zero risk to existing gate logic.

**Components:**
- `hooks/intent-sdlc.py` — add `hotfix`, `chore`, `spike` entries to `PATTERNS` and `SUGGESTIONS`; extend `no_track_msg` condition to include new intent categories
- `tests/unit/test_hooks_intent_sdlc.py` — add `TestNewIntentDetection` class covering the two scenarios mandated by the backlog item, plus chore detection

**Data Flow:**
1. User submits prompt (e.g. "emergency fix for prod")
2. `intent-sdlc.py` compiles new `hotfix` patterns at module level (already in `COMPILED_PATTERNS` via dict comprehension)
3. Scoring loop assigns score to `hotfix` category; `best = "hotfix"`
4. `SUGGESTIONS["hotfix"]` maps to `/hotfix`; `intent_cmd = "/hotfix"`
5. `no_track_msg` guard checks `best in ("implement", "fix", "hotfix", "chore", "spike")` — fires if no active Now-lane track
6. Output: `[zie-framework] intent:hotfix → /hotfix | task:none | stage:idle | next:/status | tests:unknown`

**Edge Cases:**
- "fix" and "hotfix" pattern overlap — word-boundary anchors (`\b`) on fix patterns prevent "hotfix" from matching the fix category; hotfix patterns use multi-word phrases ("prod down", "cannot wait") that don't overlap with fix single-word patterns
- `no_track_msg` for new intents — hotfix/chore/spike naturally imply no standard Now-lane task; guard fires by design when Now lane is empty, same as implement/fix
- "chore" pattern "update docs" — must not collide with general "update" language; patterns are sufficiently specific (full phrases, not single words)
- Empty or short prompts — existing `len(message) < 15` early-exit guard still applies; no change needed

**Out of Scope:**
- Adding hotfix/chore/spike to `STAGE_KEYWORDS` or `STAGE_COMMANDS` (Now-lane stage derivation — not relevant to intent detection)
- Changing the `/chore`, `/hotfix`, `/spike` command files themselves
- Changing the no-track escape-hatch message text (already lists all three tracks)
- ReDoS hardening — covered by separate backlog item (audit-intent-detect-redos)
- Pattern recompile optimization — covered by separate backlog item (audit-intent-detect-regex-recompile)
