---
approved: true
approved_at: 2026-04-04
backlog: zie-framework/backlog/model-impl-reviewer-effort-medium-to-low.md
---

# Drop impl-reviewer Effort medium → low — Design Spec

**Problem:** `skills/impl-reviewer/SKILL.md` declares `model: haiku` and `effort: medium`. The skill's own comment documents that it performs routine pattern-matching checks (AC coverage, test exists, security scanning) on haiku, with escalation to sonnet reserved for complex architectural concerns. Haiku at medium effort cannot leverage the larger token budget — the right lever for depth is model escalation, not effort on the same model.

**Approach:** Change `effort: medium` to `effort: low` in `skills/impl-reviewer/SKILL.md` frontmatter. No logic changes required — the checklist, output format, and sonnet escalation annotation are unchanged. Haiku+low is the correct pairing for pattern-matching review tasks; the existing `<!-- model: sonnet escalation note -->` in Phase 2 already documents the correct escalation path for cases that genuinely need deeper reasoning.

**Components:**
- `skills/impl-reviewer/SKILL.md` — one frontmatter key changed (`effort: medium` → `effort: low`)

**Data Flow:**
1. Claude Code reads `skills/impl-reviewer/SKILL.md` frontmatter when impl-reviewer is dispatched after each REFACTOR phase.
2. `effort: low` is selected; haiku runs with a smaller token budget appropriate to pattern-matching checks.
3. Phase 2 checklist (AC coverage, test exists, security scanning, dead code) executes identically.
4. If review detects patterns requiring deeper reasoning, the existing sonnet escalation path in Phase 2 applies — unchanged.

**Edge Cases:**
- No runtime logic depends on the `effort` value — change is safe.
- Tests that assert frontmatter fields (e.g. `test_model_effort_frontmatter.py`) must accept `low` as the valid effort for impl-reviewer; update assertions accordingly.
- ADR-022 governs effort routing: `effort: high` reserved for spec-design only; all other skills at `medium` or `low`. Changing impl-reviewer from `medium` to `low` is consistent with this rule (routine checklist task).
- ADR-017 upgraded impl-reviewer to `sonnet/medium`; ADR-030 later reverted impl-reviewer to `haiku` as default. This change targets only the `effort` field and does not touch the `model` field.

**Out of Scope:**
- Changing `model: haiku` — model selection is correct per ADR-030.
- Modifying the Phase 2 checklist steps or Phase 3 context checks.
- Changing effort for spec-reviewer or plan-reviewer.
- Introducing a config override for per-skill effort in `.config`.
