# Agentic Pipeline v2

## Problem

zie-framework has become a checklist that humans read and execute step-by-step, creating unnecessary friction at 7 approval gates across backlog→spec→plan→implement→release→retro. Each gate asks for human judgment on mechanical operations (version confirm, spec approval, plan approval) that AI reviewers already validated, making the pipeline feel long and non-agentic despite having reviewer automation underneath.

## Motivation

For zie-framework to be a truly agentic SDLC, fully-automatable steps must be automated. Currently the user experiences 1 stop per feature at only 2 decisions (title input + CHANGELOG narrative), but the UI creates 7 human interaction points due to "double-checking" a reviewer already passed. Removing these unnecessary gates reduces context bloat, eliminates compaction overhead, and enables true end-to-end autonomous feature delivery with human control at only the decision gates that matter.

## Rough Scope

**In Scope:**
- Eliminate double-human-approval in spec-design (remove step 6 draft review + step 8 manual review)
- Eliminate mechanical "confirm plan" gate in /zie-plan (auto-approve on reviewer pass)
- Make /zie-release auto-accept version suggestion (display only, no prompt)
- Replace plugin-specific agents (zie-framework:retro-format, docs-sync-check) with general-purpose agents (available in all sessions)
- Auto-commit retro ADRs and components.md updates instead of leaving for manual commit
- Add pre-flight enforcement in /zie-implement: warn if not run in `--agent` session, recommend mode

**Out of Scope:**
- Changing review logic (spec-reviewer, plan-reviewer, impl-reviewer stay the same)
- CHANGELOG approval (keep as human gate — controls public narrative)
- Backlog item content (user provides title; AI can draft Problem/Motivation but user owns it)
- Visual checks in release (if frontend exists)
