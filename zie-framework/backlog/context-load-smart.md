# context-load-smart

## Problem

Skills, commands, and agents load the same files (`.config`, `ROADMAP.md`, `decisions/*.md`, `project/context.md`) independently on every invocation. The `load-context` skill was designed to deduplicate this but is only used by `/implement`, `/plan`, and `/sprint`. The `/spec`, `/brainstorm`, `/audit` commands load ADRs and context.md independently. All three reviewer skills contain copy-pasted Phase 1 "Load Context Bundle" logic. The `subagent-context.py` hook reads ROADMAP.md on every SubagentStart, then commands read it again.

## Motivation

Token waste: each redundant read costs ~200-500 tokens. A full sprint cycle may read `ROADMAP.md` 14+ times and `.config` 15+ times. Reducing this cuts context window pressure and speeds up each command.

## Rough Scope

1. **Universal context bundle** — Make `load-context` the single entry point for ALL commands and skills. Remove duplicate ADR/context loading from `brainstorm`, `audit`, `spec-design`, and all three reviewer skills.
2. **Session-level cache** — Extend the existing `/tmp/zie-<project>-session-context-<session_id>` flag to include a content hash. Commands check the hash before re-reading; skip if unchanged within TTL (600s).
3. **Reviewer dedup** — Replace the copy-pasted Phase 1 in spec-reviewer, plan-reviewer, impl-reviewer with a shared `context_bundle` parameter that the calling command passes in.
4. **ROADMAP session cache** — The `subagent-context.py` hook already reads ROADMAP. Pass its result via `additionalContext` so commands don't re-read it.