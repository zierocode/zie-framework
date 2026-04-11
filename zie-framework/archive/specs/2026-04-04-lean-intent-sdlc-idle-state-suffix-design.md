---
approved: true
approved_at: 2026-04-04
---

# Lean Intent SDLC Idle State Suffix — Design Spec

**Problem:** `intent-sdlc.py` unconditionally appends the ~60-char SDLC state suffix (`task:none | stage:idle | next:/status | tests:unknown`) to every prompt injection during idle state, which is the most common state between commands. When there is no active task and intent is unambiguous, the suffix conveys zero information and is pure overhead.

**Approach:** Make the SDLC state suffix conditional in the `_build_combined_context` block of `intent-sdlc.py`. Suppress the suffix when `stage == "idle"` AND `active_task == "none"` AND `best` is not None AND the top intent score is ≥ 2 (unambiguous). Keep the full suffix in all other cases: active task, ambiguous intent (score < 2), or any non-idle stage.

**Components:**
- `hooks/intent-sdlc.py` — add suppression condition before `parts.append(f"task:...")` line
- `tests/unit/test_intent_sdlc_early_exit.py` — add test class `TestIdleStateSuffixSuppression`

**Data Flow:**
1. Hook runs existing intent detection → `best` (top category or None), `scores` dict
2. Hook derives SDLC state → `active_task`, `stage`, `suggested_cmd`, `test_status`
3. Before appending suffix: evaluate suppress condition:
   - `suppress_suffix = (stage == "idle" and active_task == "none" and best is not None and scores.get(best, 0) >= 2)`
4. If `suppress_suffix` is True → skip `parts.append(f"task:...")` entirely
5. If `suppress_suffix` is False → append suffix as before
6. `print(json.dumps({"additionalContext": context}))` — unchanged

**Edge Cases:**
- Score == 1 (ambiguous) + idle → suffix retained (Claude needs orientation)
- Score == 0 + idle → hook exits early at `has_sdlc_keyword` gate before reaching suffix logic — no change needed
- Active task + unambiguous intent → suffix always retained (stage != "idle")
- `best` is None (no matched category) → `best is not None` check is False → `suppress_suffix` is False → suffix retained. The explicit null-check is required; do not rely on `scores.get(None, 0)` implicit behavior.
- Gate messages and no-track messages → suffix suppression does not apply; those paths already short-circuit before the suffix append

**Out of Scope:**
- Modifying the intent signal format (`intent:best → /cmd`)
- Changing pipeline gate or no-track message logic
- Suppression based on any factor other than idle + unambiguous intent score
- Changing the SDLC suffix format when it is emitted
- Any changes to other hooks
