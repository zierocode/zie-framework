# Suggestion Triggers

**Purpose:** Define trigger conditions and corresponding suggestions for `auto-decide`.

## Trigger Table

| Trigger | Condition | Suggestion | Priority |
|---------|-----------|------------|----------|
| `test_failure` | pytest exit code ≠ 0 | `/fix` + failure analysis | HIGH |
| `spec_complete` | Spec file written + approved | "Write plan? (`/plan <slug>`)" | MEDIUM |
| `plan_complete` | Plan file written + approved | "Implement? (`/implement`)" | MEDIUM |
| `multiple_errors` | ≥3 similar errors in output | Pattern fix suggestion | HIGH |
| `session_idle` | No activity >5min | "Continue working?" | LOW |
| `uncommitted_changes` | git status shows M/D at Stop | "Commit changes before ending session" | MEDIUM |
| `coverage_stale` | .coverage missing or stale | "Run `make test-unit` to update coverage" | LOW |

## Trigger Detection

### test_failure

```python
def detect_test_failure(tool_result):
    """Detect test failure from Bash tool result."""
    if tool_result.get("tool") != "Bash":
        return False
    if "pytest" not in tool_result.get("command", ""):
        return False
    return tool_result.get("exit_code", 0) != 0
```

### spec_complete

```python
def detect_spec_complete(event, roadmap):
    """Detect spec completion from ROADMAP lane change."""
    # Check if item moved from Next → Ready
    # Check if spec file created in zie-framework/specs/
    pass
```

### multiple_errors

```python
def detect_multiple_errors(tool_result):
    """Detect 3+ similar errors in output."""
    error_pattern = re.compile(r"(ERROR|FAILED|AssertionError)", re.IGNORECASE)
    errors = error_pattern.findall(tool_result.get("output", ""))
    return len(errors) >= 3
```

## Suggestion Frequency

| Rule | Value |
|------|-------|
| Max suggestions per session | 3 |
| Cooldown between suggestions | 5 minutes |
| User action resets cooldown | Yes |
| HIGH priority triggers bypass cooldown | Yes |

## Skip Mechanism

Users can skip suggestions by:
1. Typing "skip"
2. Continuing with another command
3. Explicitly dismissing the suggestion

**Hook output format:**
```json
{
  "additionalContext": "## Suggestion\n\n**Detected:** <condition>\n\n**Recommended action:** <action>\n\n> Skip: type \"skip\" or continue"
}
```
