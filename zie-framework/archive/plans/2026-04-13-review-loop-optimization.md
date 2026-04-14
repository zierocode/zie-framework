---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
---

# review-loop-optimization — Implementation Plan

## Goal

Fix contradictory max-iterations messages, unify sprint/manual retry semantics, and remove speculative file-existence checks from reviewers.

## Architecture

No architecture changes — this is a consistency fix across 4 skill files and 1 command file.

## Tech Stack

- Markdown skills (spec-reviewer, plan-reviewer, impl-reviewer)
- Markdown commands (sprint)

### Task 1: Fix max-iterations contradiction in spec-reviewer

**Files**: `skills/spec-reviewer/SKILL.md`

**Steps**:
1. Change "invoked 3 times" to "invoked 2 times" in the Max Iterations Reached block
2. Verify Notes section already says "Max 2 total iterations"

**AC**:
- Max Iterations Reached block says "invoked 2 times"
- Notes section says "Max 2 total iterations"
- Both values are consistent

### Task 2: Fix max-iterations contradiction in plan-reviewer

**Files**: `skills/plan-reviewer/SKILL.md`

**Steps**:
1. Change "invoked 3 times" to "invoked 2 times" in the Max Iterations Reached block
2. Verify Notes section already says "Max 2 total iterations"

**AC**:
- Max Iterations Reached block says "invoked 2 times"
- Notes section says "Max 2 total iterations"
- Both values are consistent

### Task 3: Unify sprint retry semantics

**Files**: `commands/sprint.md`

**Steps**:
1. In Phase 1 spec-reviewer section: Change "1 pass, then re-check once" to "Max 2 total iterations: initial scan + 1 confirm pass"
2. This matches the manual `/spec` command semantics

**AC**:
- Sprint spec-reviewer section explicitly states "Max 2 total iterations"
- Consistent with manual flow

### Task 4: Remove speculative file-existence checks

**Files**: `skills/spec-reviewer/SKILL.md`, `skills/plan-reviewer/SKILL.md`

**Steps**:
1. In spec-reviewer Phase 3, item 1: Change "list any named component files that don't exist" to "list any named component files that don't exist and are not marked 'Create' in the spec"
2. In plan-reviewer Phase 3, item 1: Change "list any file-map files that don't exist" to "list any file-map files that don't exist and are not marked 'Create'"
3. Leave impl-reviewer Phase 3, item 1 unchanged (impl checks real files)

**AC**:
- spec-reviewer skips "Create" files in file-existence check
- plan-reviewer skips "Create" files in file-existence check
- impl-reviewer file-existence check unchanged