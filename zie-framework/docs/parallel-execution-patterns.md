# Parallel Execution Patterns

Best practices for parallel execution in zie-framework.

## When to Parallelize

| Scenario | Safe? | Rationale |
|----------|-------|-----------|
| Tasks write to different files | ✅ Yes | No conflict possible |
| Tasks read-only (no writes) | ✅ Yes | No side effects |
| Agents with `run_in_background: true` | ✅ Yes | True async, no blocking |
| Tasks with `<!-- depends_on: none -->` | ✅ Yes | Explicitly independent |
| Quality checks (docs-sync + TODO scan) | ✅ Yes | Different output, read-only |
| Context bundle loading | ✅ Yes | Read-only, cached |

## When NOT to Parallelize

| Scenario | Safe? | Rationale |
|----------|-------|-----------|
| Tasks write to same file | ❌ No | Write conflict, data loss |
| Tasks share mutable state | ❌ No | Race condition possible |
| Agents without `run_in_background` | ❌ No | Blocking, no benefit |
| Tasks with circular `depends_on` | ❌ No | Deadlock |
| API rate-limited operations | ❌ No | Hit rate limit, failures |
| Sequential build steps (A → B → C) | ❌ No | B depends on A output |

## Limits

- **Max parallel tasks:** 4
- **Max parallel Agents:** 4
- **File conflicts:** Automatically detected and serialized

## Dependency Annotation Syntax

```markdown
## Task 1: Add SDLC_STAGES constant
<!-- depends_on: none -->

## Task 2: Use SDLC_STAGES in check_impl_files
<!-- depends_on: Task 1 -->
```

## File Conflict Detection

Before launching parallel tasks, the system checks for overlapping output files.
If detected, conflicting tasks are automatically serialized with a warning.
