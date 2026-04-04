# Spec: docs-sync-consolidate

**status:** draft
**slug:** docs-sync-consolidate
**date:** 2026-04-04

---

## Problem

The docs-sync check exists in three separate forms:

1. **`commands/zie-retro.md`** — inline Markdown prose (lines 66–81, ~16 lines) describing step-by-step how to glob commands/skills/hooks, compare to CLAUDE.md/README.md, and auto-update.
2. **`commands/zie-release.md`** — inline Bash one-liner (`python3 -c "..."`) in Pre-Gate-1 that checks commands/skills vs CLAUDE.md/README.md. Does **not** check hooks.
3. **`skills/docs-sync-check/SKILL.md`** — dedicated skill that already covers all three check types (commands, skills, hooks). Currently marked `deprecated: true` because the logic was moved inline.

Behavioral drift is already present: the release Bash snippet does not verify hooks, creating a gap. Three maintenance points guarantee further divergence over time.

---

## Solution

Re-activate `skills/docs-sync-check/SKILL.md` as the single authoritative source. Invoke it via `Skill(zie-framework:docs-sync-check)` from both `zie-retro` and `zie-release`, replacing their respective inline implementations.

**`zie-retro.md`**: Replace the "Check docs sync inline" block (lines 66–81, ~16 lines) with a single `Skill(zie-framework:docs-sync-check)` invocation.

**`zie-release.md`**: Replace the Pre-Gate-1 Bash one-liner block with a `Skill(zie-framework:docs-sync-check)` invocation. Preserve the graceful fallback: if Skill unavailable → print `[zie-framework] docs-sync-check unavailable — skipping` and continue. Keep the `make docs-sync` manual fallback reference.

**`skills/docs-sync-check/SKILL.md`**: Remove `deprecated` flag and deprecation notice. Verify coverage of all three check types (commands, skills, hooks) — already present in the current skill body.

### Test Suite Impact

Several existing tests assert the current (pre-consolidation) inline behavior. These must be updated:

| File | Test | Required Change |
|------|------|-----------------|
| `test_docs_sync_check_general_agent.py` | `test_release_uses_inline_bash_for_docs_sync` | Update assertion: allow `Skill(` in place of `python3 -c` |
| `test_docs_sync_check_general_agent.py` | `test_retro_uses_general_purpose_for_docs_sync` | Update assertion: accept `Skill(zie-framework:docs-sync-check)` instead of "general-purpose" prose |
| `test_docs_sync_check_general_agent.py` | `test_docs_sync_inline_instructions_in_release` | Update: `CLAUDE.md`/`README.md` references may now live in skill, not inline in release |
| `test_docs_sync_check_general_agent.py` | `test_docs_sync_inline_instructions_in_retro` | Same — references live in skill |
| `test_release_lean_fallback.py` | `test_skip_message_present` | Preserve: fallback skip message must remain in release |
| `test_release_lean_fallback.py` | `test_manual_check_reference_present` | Preserve: `make docs-sync` reference must remain in release |
| `test_model_effort_frontmatter.py` | `skills/docs-sync-check/SKILL.md` entry | Preserve: skill file must still exist with haiku/low |

Tests that must NOT change behavior:
- `test_release_no_docs_sync_check_plugin_agent` — still passes (`subagent_type=` form forbidden, `Skill(` invocation is fine)
- `test_retro_no_docs_sync_check_plugin_agent` — still passes
- `test_blocking_fallback_comment_removed` — still passes (we do not add that string)

---

## Acceptance Criteria

1. `skills/docs-sync-check/SKILL.md` is not deprecated; covers commands, skills, and hooks checks.
2. `commands/zie-retro.md` contains `Skill(zie-framework:docs-sync-check)` and does NOT contain the inline step-by-step docs-sync prose block (the ~16-line enumeration).
3. `commands/zie-release.md` contains `Skill(zie-framework:docs-sync-check)` in the Pre-Gate-1 section; retains the `docs-sync-check unavailable` graceful fallback and `make docs-sync` manual reference.
4. `zie-release.md` does NOT contain the old `python3 -c "..."` Bash snippet for docs-sync.
5. All unit tests pass after updating the affected assertions in `test_docs_sync_check_general_agent.py`.
6. `make test-fast` green.

---

## Out of Scope

- Changes to any other hook or command.
- Modifying the skill's `allowed-tools`, `model`, or `effort` frontmatter fields.
- Adding new check categories (e.g., templates) to the skill.
- Changes to the Makefile `docs-sync:` target.
