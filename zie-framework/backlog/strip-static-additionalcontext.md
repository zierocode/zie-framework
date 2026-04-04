# Strip Static Boilerplate from Per-Event additionalContext Payloads

## Problem

Several hooks inject static boilerplate strings into `additionalContext` on every event fire: `failure-context.py` appends "Quick fix: run `make test-unit` to reproduce; check output above for root cause." on every tool failure; `sdlc-compact.py` lists all changed files line-by-line on every PostCompact; `subagent-context.py` injects ADR path hints regardless of agent type. These strings never change between sessions — they are constant instructions masquerading as dynamic context.

## Motivation

Static strings in per-event hooks re-inject the same tokens into the context window on every firing event across the entire session. CLAUDE.md content is injected once and prompt-cached at near-zero marginal cost. Moving static instructional text to CLAUDE.md eliminates repeated injections — the highest-leverage token optimization available in this codebase.

## Rough Scope

- Audit all hooks for static/constant strings in additionalContext payloads
- Move to CLAUDE.md (project-level) where appropriate, or remove if redundant
- Keep only genuinely dynamic content (branch name, last commit hash, active task) in per-event injections
- Target files: `failure-context.py`, `sdlc-compact.py`, `subagent-context.py`
