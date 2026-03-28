# Pipeline Gate Enforcement — Spec-Before-Plan, Plan-Before-Implement

## Problem

The SDLC pipeline (backlog → spec → plan → implement → release → retro) is advisory,
not enforced. Users who install the plugin can invoke `/zie-plan` without an approved
spec, or ask Claude to "start coding feature X" without entering the pipeline at all.
The intent-sdlc hook injects suggestions into additionalContext but Claude is free to
ignore them — the pipeline breaks down at the first moment of impatience.

Two failure modes observed:
1. `/zie-plan SLUG` called with no approved spec file → proceeds anyway
2. User types "let's implement X" → hook suggests `/zie-implement` but doesn't verify
   a Ready-lane plan exists before Claude starts writing code

## Motivation

Enterprise-grade development requires the pipeline to be an actual gate, not a
suggestion. If spec + plan steps can be silently skipped, the framework provides no
consistency guarantee — just optional ceremony.

Making enforcement automatic (via hooks, not commands) means users can't forget or
skip, and new users learn the pipeline by encountering it naturally.

## Rough Scope

**intent-sdlc.py — add pre-condition checks:**
- When implement intent detected: check `zie-framework/ROADMAP.md` Now lane for
  active feature slug. If none → inject blocking message (not just context):
  "No active feature in Now lane. Run /zie-backlog → /zie-spec → /zie-plan first."
- When plan intent detected: check `zie-framework/specs/` for an approved spec
  (frontmatter `approved: true`). If none → inject: "No approved spec found for this
  feature. Run /zie-spec SLUG first."

**zie-plan.md — strengthen pre-flight gate:**
- Current: checks for approved spec but can be bypassed with explicit slug arg
- Strengthen: if spec missing or `approved: false`, hard-stop with clear next-step
  message regardless of how invoked

**intent-sdlc.py — positional guidance:**
- When user prompt contains a feature name that matches a backlog item in Next lane
  but no spec exists → nudge: "Feature 'X' is in backlog. Start with /zie-spec X"
- When feature has approved spec but no Ready-lane plan → nudge: "/zie-plan X"
- When feature has Ready plan but not in Now lane → nudge: "/zie-implement"

**Tests:**
- intent-sdlc detects plan intent + no approved spec → blocks
- intent-sdlc detects implement intent + no Now-lane feature → blocks
- zie-plan hard-stops without spec regardless of arg
- False-positive rate: verify that normal conversation (not pipeline intent) doesn't
  trigger gates
