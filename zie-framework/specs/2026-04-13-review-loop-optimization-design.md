---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
clarity: 5
---

# review-loop-optimization — Reduce Reviewer Iteration Redundancy

## Problem

Three issues with the current review loops:

1. **Contradictory max-iterations**: `spec-reviewer/SKILL.md` and `plan-reviewer/SKILL.md` have "Max Iterations Reached" blocks saying "invoked 3 times" but their Notes say "Max 2 total iterations". This contradiction causes confusion.

2. **Sprint vs manual retry mismatch**: Sprint's inline reviewer caps at "1 pass, then re-check once" while manual `/spec` allows "Max 3 iterations". Same reviewer, different semantics.

3. **Speculative file-existence checks**: spec-reviewer and plan-reviewer check if component files exist in Phase 3. For specs/plans, files marked "Create" are expected not to exist — this check produces false positives.

4. **Context re-reads**: Reviewers re-load ADRs and context.md from disk on each invocation, even within the same session.

## Approach

Fix the contradictions, unify retry semantics, remove speculative checks, and ensure context_bundle passthrough.

## Components

### 1. Fix max-iterations contradiction

**Files**:
- `skills/spec-reviewer/SKILL.md` — Change "invoked 3 times" to "invoked 2 times" in the Max Iterations Reached block (line ~88)
- `skills/plan-reviewer/SKILL.md` — Change "invoked 3 times" to "invoked 2 times" in the Max Iterations Reached block (line ~117)

Both files should consistently state "Max 2 total iterations" in both the error message and the Notes.

### 2. Unify sprint vs manual retry semantics

**File**: `commands/sprint.md`
- Change "1 pass, then re-check once" to explicitly state "Max 2 total iterations: initial scan + 1 confirm pass"
- This matches the manual flow semantics

**File**: `skills/spec-design/SKILL.md`
- Ensure "Max 3 iterations" is changed to "Max 2 iterations" to match the reviewer's actual cap

### 3. Remove speculative file-existence checks

**Files**:
- `skills/spec-reviewer/SKILL.md` — Phase 3, item 1: Add qualifier: "list any named component files that don't exist and are **not** marked 'Create' in the spec. Files marked 'Create' are expected not to exist."
- `skills/plan-reviewer/SKILL.md` — Phase 3, item 1: Same qualifier: "list any file-map files that don't exist and are **not** marked 'Create'."
- `skills/impl-reviewer/SKILL.md` — Phase 3, item 1: Keep as-is (impl-reviewer checks actual files that should exist)

### 4. Pass context_bundle to avoid re-reads

Already covered by `context-load-smart` spec — this item is a dependency, not a separate change. Once all commands pass `context_bundle` to reviewers, the disk-read fallback in Phase 1 becomes a safety net rather than the primary path.

## Data Flow

No data flow changes — this is a consistency and efficiency fix.

## Edge Cases

- **Reviewer invoked standalone**: If no `context_bundle` is provided, the reviewer falls back to disk reads (existing behavior). No breakage.
- **Sprint autonomous mode**: Unified 2-iteration cap applies to both manual and autonomous flows.

## Out of Scope

- Changing the reviewer output format
- Adding new review checks
- Modifying the approval flow (reviewer-gate.py)

## Testing

- Unit test: spec-reviewer max-iterations error message says "2" not "3"
- Unit test: plan-reviewer max-iterations error message says "2" not "3"
- Unit test: file-existence check skips "Create" files in spec-reviewer
- Unit test: file-existence check skips "Create" files in plan-reviewer