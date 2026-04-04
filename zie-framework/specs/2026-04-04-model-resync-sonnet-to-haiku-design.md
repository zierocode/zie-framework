---
approved: true
approved_at: 2026-04-04
---

# Downgrade /resync Model: sonnet → haiku — Design Spec

**Problem:** `commands/resync.md` declares `model: sonnet` and `effort: medium`. The main resync thread is a mechanical coordinator — it reads Explore subagent output and writes structured markdown docs. The heavy reasoning work (codebase understanding) is done by the Explore subagent, not by the resync command itself, so Sonnet is overkill for the coordinator role.

**Approach:** Change a single frontmatter key in `commands/resync.md` — `model: sonnet` → `model: haiku`. Keep `effort: medium` to preserve output structure quality (haiku benefits from the extra budget when writing multi-section markdown). No logic changes; the Explore subagent invocation and all steps remain identical. If testing reveals haiku+medium produces well-structured docs, dropping effort to `low` is a follow-up option — out of scope here.

**Components:**
- `commands/resync.md` — one frontmatter key changed (`model` line only)

**Data Flow:**
1. User invokes `/resync`.
2. Claude Code reads `commands/resync.md` frontmatter.
3. `model: haiku` is selected instead of Sonnet.
4. `effort: medium` is unchanged — haiku runs with medium effort.
5. Steps execute identically: Explore subagent scans codebase → resync coordinator reads report → drafts four knowledge docs → presents to user → writes on approval → recomputes knowledge hash.

**Edge Cases:**
- The Explore subagent model is not controlled by the command frontmatter — it is not affected by this change.
- No runtime logic depends on the model key; the change is safe to all idempotent re-runs.
- **Confirmed:** `tests/unit/test_model_effort_frontmatter.py` contains an `EXPECTED` dict (line 27) that maps `"commands/resync.md"` to `("sonnet", "medium")`. `TestExpectedValues.test_correct_model_values` (line 105) asserts the exact value. This test **will fail** after the frontmatter change and must be updated: change line 27 from `("sonnet", "medium")` to `("haiku", "medium")`. No other test file asserts a specific model value for `resync.md`; `test_model_routing_v2.py` covers only `release.md` and `impl-reviewer/SKILL.md`.

**Out of Scope:**
- Changing `effort: medium` to `effort: low` (deferred; test first).
- Changing the model of the Explore subagent inside the resync steps.
- Changing the `/resync` step logic, narrative, or output format.
- Updating any other command's model or effort setting.
- Introducing a `.config` override for per-command model selection.
