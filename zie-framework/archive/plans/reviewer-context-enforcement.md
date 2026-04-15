---
approved: true
spec: specs/2026-04-14-reviewer-context-enforcement-design.md
---

# Implementation Plan: Reviewer Context Bundle Enforcement

## Overview

Make `context_bundle` parameter required across all 3 reviewer skills, removing disk fallback code paths and standardizing caller behavior.

## Tasks

### Phase 1: Update Reviewer Skills

1. **Update `skills/spec-reviewer/SKILL.md`** (least called - start here)
   - Make `context_bundle` required parameter
   - Remove disk fallback code
   - Add validation error:
     ```
     ERROR: context_bundle is required. Reviewers no longer support disk fallback.
     Please pass context_bundle with spec_content and plan_content.
     ```
   - Extract `spec_content` and `plan_content` from bundle directly

2. **Update `skills/plan-reviewer/SKILL.md`**
   - Same changes as spec-reviewer
   - Make `context_bundle` required
   - Remove disk fallback

3. **Update `skills/impl-reviewer/SKILL.md`** (most called - do last)
   - Same changes as above
   - Make `context_bundle` required
   - Remove disk fallback

### Phase 2: Update Callers

4. **Audit all reviewer callers**
   - Search for all invocations of the 3 reviewers
   - Identify callers not passing `context_bundle`

5. **Update `commands/sprint.md`**
   - Build context bundle before calling reviewers
   - Pass `context_bundle` with `spec_content` and `plan_content`

6. **Update `commands/implement.md`**
   - Build context bundle before calling impl-reviewer
   - Pass `context_bundle`

7. **Update any other callers**
   - Ensure all callers pass `context_bundle`

### Phase 3: Testing

8. **Unit tests**
   - Verify error raised when `context_bundle` missing
   - Verify success when `context_bundle` provided

9. **Integration tests**
   - Call each reviewer without bundle → verify error
   - Call each reviewer with bundle → verify success
   - Test all reviewer invocations in sprint flow

10. **Token audit**
    - Measure token savings (target: ~1.2w tokens per invocation)

## Acceptance Criteria

- [ ] All 3 reviewers reject calls without `context_bundle`
- [ ] Zero disk read fallbacks in reviewer code
- [ ] All callers updated to pass `context_bundle`
- [ ] Token savings ~1.2w tokens per invocation
- [ ] All tests passing

## Estimated Effort

- Phase 1: ~1.5 hours (3 reviewers × 30 min)
- Phase 2: ~1.5 hours (audit + update callers)
- Phase 3: ~1 hour
- **Total: ~4 hours**
