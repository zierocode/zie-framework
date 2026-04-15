---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
clarity: 5
---

# context-load-smart — Universal Context Loading Deduplication

## Problem

Skills, commands, and agents load `.config`, `ROADMAP.md`, `decisions/*.md`, and `project/context.md` independently on every invocation. The `load-context` skill was designed to deduplicate ADR/context loading but is only used by `/implement`, `/plan`, and `/sprint`. The `/spec`, `/brainstorm`, `/audit` commands load ADRs and context independently. All three reviewer skills contain copy-pasted Phase 1 "Load Context Bundle" logic. The `subagent-context.py` hook reads ROADMAP on every SubagentStart, then commands read it again.

A full sprint cycle reads `ROADMAP.md` 14+ times and `.config` 15+ times, wasting ~3,000-7,000 tokens of context window.

## Approach

Make `load-context` the universal entry point for context loading. Extend the session cache to cover all shared reads. Remove duplicate loading from skills and commands that bypass `load-context`.

## Components

### 1. Universal load-context entry point

**Current**: Only `/implement`, `/plan`, `/sprint` invoke `Skill(zie-framework:load-context)`.
**Change**: All commands and skills that need ADRs or project context must call `Skill(zie-framework:load-context)` first and pass the result downstream.

Files to update:
- `commands/spec.md` — add `Skill(zie-framework:load-context)` call before spec-design
- `commands/audit.md` — add `Skill(zie-framework:load-context)` call before audit
- `skills/brainstorm/SKILL.md` — replace direct ADR reads with `Skill(zie-framework:load-context)`
- `skills/spec-design/SKILL.md` — replace direct ADR reads with `context_bundle` parameter from caller

### 2. Session content-hash cache

**Current**: `subagent-context.py` uses `/tmp/zie-<project>-session-context-<session_id>` flag (writes "cached" string, checks mtime < 7200s).
**Change**: Extend to store a content hash of the loaded context. Commands check the hash before re-reading.

File: `hooks/subagent-context.py`
- Add content-hash field to cache file (SHA-256 of ADR summary + context.md concatenated)
- On SubagentStart: if cache exists AND hash matches AND mtime < 600s → skip inject
- On context load: if cache exists AND hash matches → return cached bundle immediately

### 3. Reviewer context_bundle passthrough

**Current**: All three reviewer skills have copy-pasted Phase 1 "Load Context Bundle" with identical disk-read fallback logic.
**Change**: All reviewers accept `context_bundle` as a parameter. If provided, skip Phase 1 entirely. The calling command always passes the bundle from `load-context`.

Files to update:
- `skills/spec-reviewer/SKILL.md` — Phase 1 becomes: "If context_bundle provided, use it. Otherwise, call Skill(zie-framework:load-context)."
- `skills/plan-reviewer/SKILL.md` — same change
- `skills/impl-reviewer/SKILL.md` — same change

### 4. ROADMAP session cache

**Current**: `subagent-context.py` reads ROADMAP and emits a summary line. Commands then read ROADMAP again independently.
**Change**: `subagent-context.py` already injects the active feature via `additionalContext`. Commands should check `additionalContext` before re-reading ROADMAP. This is a documentation/behavior change, not a code change — commands that read ROADMAP for the Now lane should prefer the already-injected context when available.

Files to update:
- `commands/implement.md` — note that ROADMAP is injected by session-resume hook, only re-read if Now lane changes
- `commands/sprint.md` — same note
- `commands/plan.md` — same note

## Data Flow

```
Session Start
  └→ session-resume.py injects: project, version, active feature, backlog count
  └→ subagent-context.py injects: active feature, task, ADR count

Command Invocation
  └→ Skill(zie-framework:load-context) → checks cache → returns context_bundle
  └→ Command passes context_bundle to reviewer skills
  └→ Reviewer skills: if context_bundle → skip Phase 1

Cache Invalidation
  └→ Content hash mismatch → cache miss → reload
  └→ TTL > 600s → cache expired → reload
  └→ New session → no cache → always load
```

## Edge Cases

- **Cache file missing**: Falls back to disk read (existing behavior)
- **ADR-000-summary.md missing**: Falls back to reading all `decisions/*.md` (existing behavior)
- **project/context.md missing**: Returns empty `context_content` (existing behavior)
- **Parallel agent spawns**: Each agent gets its own session context via `additionalContext`; cache is session-scoped so no cross-session contamination

## Out of Scope

- Changing the `zie-memory` MCP integration (separate concern)
- Adding new ADR files (this is a refactoring task)
- Modifying hook event structure or protocol

## Testing

- Unit test: `load-context` cache hit/miss with content hash
- Unit test: reviewer skills skip Phase 1 when context_bundle provided
- Unit test: subagent-context.py content hash comparison
- Integration test: full sprint cycle reads ROADMAP fewer times (measure before/after)