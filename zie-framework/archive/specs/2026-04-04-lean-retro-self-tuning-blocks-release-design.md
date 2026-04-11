---
approved: false
backlog: backlog/lean-retro-self-tuning-blocks-release.md
---

# Lean Retro — Self-Tuning Proposals Non-Blocking — Design Spec

**Problem:** The `/retro` command's "Self-tuning proposals" section contains a synchronous interactive prompt (`"Apply? Type 'apply' to write to .config, or skip."`) mid-stream. This blocks the automated release pipeline: when `/sprint` or any automated caller runs `/retro`, the command stalls waiting for user input before the auto-commit step can execute.

**Approach:**
1. Move the self-tuning proposals print to the final printed step of retro (after all blocking work: ADRs, ROADMAP update, Done-rotation, auto-commit, knowledge update, brain storage).
2. Remove the interactive wait entirely (`"Apply? Type 'apply'..."` prompt removed).
3. Replace with a non-blocking advisory message pointing the user to `/chore` to apply changes manually.
4. Add a `self_tuning_enabled` config key (default `true`) to allow opt-out without touching the command file.

**Config key:**

| Key | Default | Values | Description |
| --- | --- | --- | --- |
| `self_tuning_enabled` | `true` | `true`, `false` | When `false`, skip the self-tuning proposals section entirely in `/retro`. |

**Components:**
- Modify: `commands/retro.md` — reorder self-tuning section to final printed step; remove interactive wait; replace with advisory message; read `self_tuning_enabled` from `.config` (default `true`).
- Modify: `zie-framework/.config` — no change needed at runtime (key is optional, defaults to `true`).
- Modify: `CLAUDE.md` — add `self_tuning_enabled` row to the Hook Configuration table.
- Tests: `tests/unit/test_retro_self_tuning.py` — add test asserting advisory message format and that the interactive prompt string is absent from the command text; add test for `self_tuning_enabled: false` skip path.

**Acceptance Criteria:**
- [ ] Self-tuning proposals section is the last printed block in `/retro` (after auto-commit, knowledge update, brain storage, archive prune, and suggest-next)
- [ ] No interactive prompt (`"Apply?"` / `"Type 'apply'"`) appears anywhere in the self-tuning section
- [ ] Advisory message is printed in the form: `"[zie-framework] self-tuning: N proposal(s) — run /chore to apply. See self-tuning proposals above."`
- [ ] When `self_tuning_enabled: false` in `.config`, the section prints `"Self-tuning: disabled"` and skips immediately
- [ ] When `.config` is absent, self-tuning still runs (default `true`)
- [ ] All upstream retro steps (ADRs, ROADMAP, auto-commit) are unaffected
- [ ] Existing `test_retro_self_tuning.py` tests still pass (logic in `utils_self_tuning.py` unchanged)
- [ ] `CLAUDE.md` Hook Configuration table includes `self_tuning_enabled` row

**Out of Scope:**
- Auto-applying self-tuning proposals without user action
- Moving proposal computation logic out of the retro command
- Any change to `utils_self_tuning.py` proposal-building logic
- New `/chore` command implementation (advisory pointer only)
