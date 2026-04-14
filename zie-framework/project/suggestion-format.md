# Suggestion Output Format

**Purpose:** Define the standard format for auto-decide suggestions.

## Markdown Template

```markdown
## Suggestion

**Detected:** <condition description>

**Recommended action:** <command or action>

**Why:** <brief rationale>

> Skip: type "skip" or continue with another command
```

## Example Outputs

### Test Failure

```markdown
## Suggestion

**Detected:** 3 tests failing (AssertionError in test_auto_inject)

**Recommended action:** Run `/fix` to debug and fix failing tests

**Why:** Failing tests block progress to next phase

> Skip: type "skip" or continue with another command
```

### Spec Complete

```markdown
## Suggestion

**Detected:** Spec approved for auto-learn

**Recommended action:** Run `/plan auto-learn` to draft implementation plan

**Why:** Plan required before implementation can begin

> Skip: type "skip" or continue with another command
```

### Multiple Errors

```markdown
## Suggestion

**Detected:** 5 similar errors in test output (pattern: `KeyError: 'context_bundle'`)

**Recommended action:** Check if `context_bundle` is being passed to all reviewers

**Why:** Same error in multiple files suggests a common cause

> Skip: type "skip" or continue with another command
```

## JSON Output (Hook Protocol)

For PostToolUse hooks, suggestions are injected via `additionalContext`:

```json
{
  "additionalContext": "## Suggestion\n\n**Detected:** 3 tests failing\n\n**Recommended action:** /fix\n\n> Skip: type \"skip\" or continue"
}
```

## Formatting Rules

1. **Header:** Always `## Suggestion`
2. **Detected:** 1-2 sentences describing the trigger condition
3. **Recommended action:** Specific command or action
4. **Why:** Optional, 1 sentence rationale
5. **Skip instruction:** Always included, formatted as blockquote

## Priority Levels

| Priority | Cooldown Bypass | Frequency Cap |
|----------|-----------------|---------------|
| HIGH | Yes | No |
| MEDIUM | No | Yes |
| LOW | No | Yes |

**HIGH:** test_failure, multiple_errors
**MEDIUM:** spec_complete, plan_complete, uncommitted_changes
**LOW:** session_idle, coverage_stale
