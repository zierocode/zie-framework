---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
---

# context-load-smart — Implementation Plan

## Goal

Reduce redundant context loading across skills, commands, and agents by making `load-context` the universal entry point and adding session content-hash caching.

## Architecture

- Session-level content-hash cache in `/tmp/zie-<project>-context-cache-<session_id>` with SHA-256 + TTL
- All commands/skills that need ADRs or project context call `Skill(zie-framework:load-context)` first
- All reviewer skills accept `context_bundle` parameter and skip Phase 1 when provided

## Tech Stack

- Python hooks (subagent-context.py, session-resume.py)
- Markdown skills (load-context, spec-reviewer, plan-reviewer, impl-reviewer)
- Markdown commands (spec, audit, implement, plan, sprint)

### Task 1: Add content-hash cache to subagent-context.py

**Files**: `hooks/subagent-context.py`

**Steps**:
1. After writing the session flag, also write a content hash file at `/tmp/zie-<project>-context-hash-<session_id>` containing SHA-256 of (`ADR-000-summary.md` content + `project/context.md` content)
2. On SubagentStart: check if hash file exists AND hash matches current content AND mtime < 600s → skip re-injection
3. On hash mismatch or expired TTL: re-inject and update hash file

**AC**:
- Unit test: cache hit when hash matches and TTL < 600s
- Unit test: cache miss when hash differs
- Unit test: cache miss when TTL > 600s

### Task 2: Add load-context call to spec, audit, brainstorm

**Files**: `commands/spec.md`, `skills/brainstorm/SKILL.md`

**Steps**:
1. In `commands/spec.md`: Add `Skill(zie-framework:load-context)` call before spec-design invocation, pass `context_bundle` downstream
2. In `skills/brainstorm/SKILL.md`: Replace direct `decisions/ADR-000-summary.md` reads with `Skill(zie-framework:load-context)` call at Phase 1 start
3. In `skills/spec-design/SKILL.md`: Accept `context_bundle` parameter; if provided, skip ADR loading in Phase 1

**AC**:
- `/spec` command invokes load-context before spec-design
- `brainstorm` skill invokes load-context instead of direct file reads
- spec-design accepts context_bundle parameter

### Task 3: Simplify reviewer Phase 1 to use context_bundle

**Files**: `skills/spec-reviewer/SKILL.md`, `skills/plan-reviewer/SKILL.md`, `skills/impl-reviewer/SKILL.md`

**Steps**:
1. In all three reviewer skills: Change Phase 1 from copy-pasted disk-read logic to a single line: "If context_bundle provided → use it. Otherwise, call Skill(zie-framework:load-context)."
2. Remove the duplicated `get_cached_adrs` / `write_adr_cache` / `decisions/ADR-000-summary.md` fallback blocks from all three files
3. Add `context_bundle` to `argument-hint` in frontmatter

**AC**:
- All three reviewer skills have single-line Phase 1 with context_bundle fast path
- No duplicated ADR loading logic remains in reviewer skills
- Reviewers work correctly when called with and without context_bundle

### Task 4: Document ROADMAP session cache optimization

**Files**: `commands/implement.md`, `commands/sprint.md`, `commands/plan.md`

**Steps**:
1. Add a comment in each command's pre-flight section: "<!-- context: ROADMAP already injected by session-resume hook; re-read only if Now lane may have changed -->"
2. No code change — this is a documentation hint for future optimization

**AC**:
- Comments added to all three command files