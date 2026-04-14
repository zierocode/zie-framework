---
approved: true
backlog: backlog/combined-nudge-checks.md
---

# Combined Nudge Checks — Design Specification

## Summary

Consolidate 3 nudge conditions into a single git log pass within `stop-handler.py`: parse once, distribute to all nudge checks.

## Problem Statement

Current state (in stop-guard.py lines 80-120):
- 3 nudge conditions each run `git log --oneline` independently:
  1. Status nudge
  2. Nudges list check
  3. Pipeline status check
- 3 git log calls per Stop event
- 30min TTL but still 3× redundant work

Result: ~100 tokens wasted per Stop event.

## Goals

| Goal | Success Metric |
|------|----------------|
| Single git log call | Git log called once per Stop |
| Parse once, use many times | Parsed result shared across all nudge checks |
| Preserve all nudge conditions | No nudge functionality lost |

## Non-Goals

- Changing nudge conditions or logic
- Modifying nudge TTL behavior
- Adding new nudge conditions

## Design

### Combined Nudge Check Structure

Integrated into `hooks/stop-handler.py`:

```python
def get_git_log_parsed():
    """
    Single git log call, parsed into structured format.
    Returns list of commit dicts.
    """
    result = subprocess.run(
        ["git", "log", "--oneline", "-50"],  # Last 50 commits
        capture_output=True,
        text=True
    )
    
    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        # Parse: "abc1234 commit message here"
        parts = line.split(" ", 1)
        commits.append({
            "hash": parts[0] if len(parts) > 0 else "",
            "message": parts[1] if len(parts) > 1 else ""
        })
    
    return commits

def check_nudges(git_status, commits):
    """
    All nudge conditions evaluated from single git log pass.
    """
    nudges = []
    
    # Nudge 1: Uncommitted changes (uses git_status, not git log)
    if git_status:
        nudges.append(f"💡 Uncommitted changes:\n{git_status}")
    
    # Nudge 2: Pipeline status (analyzes commits)
    pipeline_nudge = check_pipeline_from_commits(commits)
    if pipeline_nudge:
        nudges.append(pipeline_nudge)
    
    # Nudge 3: Stale branch hint (analyzes commits)
    stale_nudge = check_stale_branch_from_commits(commits)
    if stale_nudge:
        nudges.append(stale_nudge)
    
    return nudges

def check_pipeline_from_commits(commits):
    """
    Check pipeline status from commit history.
    - Look for WIP commits
    - Check for unmerged branches
    - Verify release cadence
    """
    # Logic from original stop-pipeline-guard.py
    # Now using pre-parsed commits instead of re-running git log
    
    wip_commits = [c for c in commits if "WIP" in c["message"]]
    if wip_commits:
        return f"💡 WIP commits detected: {len(wip_commits)}"
    
    return None

def check_stale_branch_from_commits(commits):
    """
    Check if branch is stale (no recent commits).
    """
    # Logic from original compact-hint or similar
    if len(commits) == 0:
        return "💡 No recent commits — consider pushing or merging"
    
    return None
```

### Integration with Stop Handler

This spec is a refinement of `stop-handler-merge`:

```python
def main():
    # Single calls for all checks
    git_status = get_git_status()
    commits = get_git_log_parsed()
    
    # All nudges evaluated from single data pass
    nudges = check_nudges(git_status, commits)
    
    if nudges:
        for nudge in nudges:
            print(nudge)
        write_log(nudges)
        exit(1)
    
    exit(0)
```

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `hooks/stop-handler.py` | Modify | Add combined nudge checks |

**Note:** This spec is implemented as part of `stop-handler-merge` since the nudge consolidation happens within the unified handler.

## Dependencies

- **stop-handler-merge**: Required (provides stop-handler.py structure)

## Testing Plan

1. **Unit**: Git log parsing correctness
2. **Integration**: Each nudge condition fires correctly
3. **Performance**: Verify only 1 git log call per Stop
4. **Token audit**: Measure savings vs 3× git log calls

## Rollout Plan

1. Implement in stop-handler.py (alongside merge spec)
2. Test all 3 nudge conditions
3. Verify single git log call
4. Measure token savings

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Nudge condition missed | Test each condition independently |
| Parse error on git log | Handle malformed output gracefully |
| Performance regression | Benchmark: 1 call should be faster than 3 |

## Open Questions

None — scope is well-defined.
