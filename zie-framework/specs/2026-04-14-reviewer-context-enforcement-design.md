---
approved: true
backlog: backlog/reviewer-context-enforcement.md
---

# Reviewer Context Bundle Enforcement — Design Specification

## Summary

Make `context_bundle` parameter required across all reviewer skills, removing disk fallback code paths and standardizing caller behavior.

## Problem Statement

Current state:
- Fast-path context_bundle exists but is optional
- Disk fallback code paths remain in 3 reviewer skills
- Callers inconsistent with context_bundle passing
- ~300w tokens dead code bloat
- Reviewers re-read from disk when bundle missing (~1.2w tokens per invocation)

## Goals

| Goal | Success Metric |
|------|----------------|
| Make context_bundle required | All 3 reviewers reject calls without bundle |
| Remove disk fallback | Zero disk read fallbacks in reviewer code |
| Standardize callers | All callers pass context_bundle |
| Reduce token waste | Save ~1.2w tokens per reviewer invocation |

## Non-Goals

- Changing reviewer logic or approval criteria
- Modifying context bundle schema

## Design

### Affected Skills

| Skill | Current Behavior | New Behavior |
|-------|------------------|--------------|
| `skills/plan-reviewer/SKILL.md` | context_bundle optional, disk fallback | context_bundle required, error if missing |
| `skills/impl-reviewer/SKILL.md` | context_bundle optional, disk fallback | context_bundle required, error if missing |
| `skills/spec-reviewer/SKILL.md` | context_bundle optional, disk fallback | context_bundle required, error if missing |

### Validation Error

When context_bundle is missing:
```
ERROR: context_bundle is required. Reviewers no longer support disk fallback.
Please pass context_bundle with spec_content and plan_content.
```

### Code Changes Pattern

Each reviewer skill follows this pattern:

**Before:**
```python
def review(context_bundle=None, spec_path=None, plan_path=None):
    if context_bundle:
        spec_content = context_bundle.get("spec_content")
        plan_content = context_bundle.get("plan_content")
    else:
        # Disk fallback (~100 lines of dead code)
        spec_content = read_file(spec_path)
        plan_content = read_file(plan_path)
```

**After:**
```python
def review(context_bundle):
    if not context_bundle:
        raise ValueError("context_bundle is required. Reviewers no longer support disk fallback.")
    
    spec_content = context_bundle["spec_content"]
    plan_content = context_bundle["plan_content"]
    # No disk fallback
```

### Caller Updates

All callers must pass context_bundle:

```python
# commands/sprint.md, commands/implement.md, etc.
context_bundle = {
    "spec_content": read_file(spec_path),
    "plan_content": read_file(plan_path)
}
result = call_reviewer(context_bundle=context_bundle)
```

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `skills/plan-reviewer/SKILL.md` | Modify | Make context_bundle required, remove fallback |
| `skills/impl-reviewer/SKILL.md` | Modify | Make context_bundle required, remove fallback |
| `skills/spec-reviewer/SKILL.md` | Modify | Make context_bundle required, remove fallback |

## Dependencies

- **unified-context-cache**: Required (provides context_bundle pattern)

## Testing Plan

1. **Unit**: Verify error raised when context_bundle missing
2. **Integration**: Call each reviewer without bundle — verify error
3. **Integration**: Call each reviewer with bundle — verify success
4. **Token audit**: Measure token savings vs baseline

## Rollout Plan

1. Update spec-reviewer first (least called)
2. Update plan-reviewer
3. Update impl-reviewer (most called)
4. Update all callers to pass context_bundle
5. Test all reviewer invocations

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Callers broken without bundle | Update all callers in same PR |
| Backward compatibility | Breaking change intentional — document in changelog |
| Reviewer logic regression | Run full test suite for each reviewer |

## Open Questions

None — scope is well-defined.
