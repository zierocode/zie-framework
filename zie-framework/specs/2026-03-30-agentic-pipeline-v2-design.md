---
approved: true
approved_at: 2026-03-30
backlog: backlog/agentic-pipeline-v2.md
---

# Agentic Pipeline v2 — Design Spec

**Problem:** zie-framework has 7 approval gates across the SDLC pipeline (backlog→spec→plan→implement→release→retro) that ask humans to confirm mechanical operations (version confirmation, spec approval, plan approval) that AI reviewers already validated, creating unnecessary friction and making the pipeline non-agentic despite reviewer automation being present underneath.

**Approach:** Remove double-approval patterns by auto-accepting reviewer verdicts (APPROVED = automatic proceed without human re-confirmation), auto-committing retro outputs, auto-accepting version suggestions, and replacing plugin-specific subagent types with general-purpose agents. This preserves human control at decision gates (title input, CHANGELOG narrative, explicit user overrides) while eliminating redundant confirmation prompts on validated operations.

**Components:**
- `skills/zie-framework/spec-design/SKILL.md` — steps 6, 8 (remove review confirmation prompts)
- `commands/zie-plan.md` — remove approval gate after plan-reviewer returns APPROVED
- `commands/zie-release.md` — remove version confirmation prompt, auto-accept suggestion
- `commands/zie-retro.md` — auto-commit ADRs + components.md at end; replace Agent(subagent_type="zie-framework:retro-format") with general-purpose agent
- `commands/zie-implement.md` — add pre-flight warning if not running in `--agent` session
- `hooks/` — (implied) verify docs-sync-check can run as general-purpose agent instead of plugin-specific type
- Test coverage for each affected command's new auto-path

**Data Flow:**

1. **spec-design flow (steps 5→7):**
   - Step 5: Write spec to disk → call spec-reviewer subagent
   - `spec-reviewer` returns verdict
   - **NEW:** If APPROVED → skip step 6 prompt ("Does this look right?"), proceed directly to step 7 (save to GitHub)
   - Step 7: Git commit + push spec
   - **NEW:** Step 8 no longer asks "Ask user to review?" — reviewer approval IS the gate
   - → Return success + spec URL

2. **zie-plan flow (approval stage):**
   - Write plan to disk → call plan-reviewer subagent
   - `plan-reviewer` returns verdict
   - **NEW:** If APPROVED → auto-write frontmatter (approved: true, approved_at: TODAY) + git commit + push
   - **NEW:** "Approve this plan? (yes/re-draft/drop)" prompt removed unless user explicitly calls `/zie-plan re-draft` or `/zie-plan drop` (explicit overrides remain available)
   - → Return success + plan URL

3. **zie-release flow (version suggestion):**
   - Calculate version bump
   - **NEW:** Display "Bumped to vX.Y.Z. Send override if wrong." instead of "Confirm version? (yes/no/custom)"
   - → Continue with release pipeline (tests, merge, tag, trigger retro)
   - If user disagrees, they can send `/zie-release --bump-to=X.Y.Z` to override

4. **zie-retro flow (ADR + docs commit):**
   - User writes ADRs + edits components.md in the interactive retro
   - **NEW:** At end, automatically `git add -A && git commit -m "chore: retro vX.Y.Z" && git push origin dev`
   - **NEW:** Replace `Agent(subagent_type="zie-framework:retro-format")` with `Agent(subagent_type="general-purpose", instructions="<inline prompt>")` (same logic, general type)
   - → Return success + commit hash

5. **zie-implement flow (pre-flight warning):**
   - **NEW:** At start, check if session is `--agent zie-framework:zie-implement-mode`
   - **NEW:** If not, display warning: "⚠️ Running /zie-implement outside agent session. Recommend: `claude --agent zie-framework:zie-implement-mode`. Continue anyway? (yes/cancel)"
   - Continue as normal if user approves
   - (This is informational; does not block, since some workflows may intentionally run outside agent mode)

6. **docs-sync-check reference (post-release):**
   - Replace `Agent(subagent_type="zie-framework:docs-sync-check")` with `Agent(subagent_type="general-purpose", instructions="<inline prompt>")`
   - Inline prompt covers: verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk, return JSON summary

**Edge Cases:**

1. **spec-reviewer returns issues** → Display issues, ask user to fix and re-submit. No change to current flow.
2. **plan-reviewer returns issues** → Display issues, ask user to re-draft or drop. `/zie-plan re-draft` and `/zie-plan drop` remain available as explicit user actions.
3. **User disagrees with version suggestion** → Send `/zie-release --bump-to=X.Y.Z`. New auto-accept does not lock user out of override.
4. **zie-retro git push fails** → Catch exception, display error, offer manual commit command. Retro workflow does not block.
5. **zie-implement called outside --agent session** → Display warning but continue (non-blocking). User can choose to cancel and restart in agent mode, or proceed.
6. **General-purpose agent timeout** (replacing plugin-specific agents) → Fall back to inline synchronous logic or display error. System does not hang.
7. **Explicit `/zie-plan drop` called** → User-driven override; auto-approve logic does not apply. Plan is dropped, no commit.

**Out of Scope:**

- Changing review logic or verdict criteria for spec-reviewer, plan-reviewer, impl-reviewer (all stay the same)
- CHANGELOG approval gate (remains human-controlled; user provides narrative before release)
- Backlog item creation logic (user still provides title; AI can draft Problem/Motivation but user owns final content)
- Visual/frontend checks in release workflow
- Changing test gates or coverage thresholds (all existing test logic remains)
- Pre-release merge conflict resolution (still requires manual intervention)

