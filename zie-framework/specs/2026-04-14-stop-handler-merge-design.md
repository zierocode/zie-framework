---
approved: true
backlog: backlog/stop-handler-merge.md
---

# Stop Handler Merge — Design Specification

## Summary

Consolidate 3 sequential Stop hooks into a single `stop-handler.py` with unified logic: one git status call, combined nudge checks, single log entry.

## Problem Statement

Current state:
- 3 separate Stop hooks fire sequentially:
  1. `hooks/stop-guard.py`
  2. `hooks/stop-pipeline-guard.py`
  3. `hooks/compact-hint.py`
- Each runs `git status --short` independently
- Nudge checks run with 30min TTL independently (3× redundant checks)
- 3 git status calls per Stop event
- 3× log writes

Result: ~600 tokens wasted per Stop event; redundant I/O and condition checks.

## Goals

| Goal | Success Metric |
|------|----------------|
| Single Stop hook | One hook file, one entry point |
| One git status call | Git status called once, results shared |
| Combined nudge checks | All nudge conditions evaluated in single pass |
| Preserve all nudges | No nudge functionality lost |

## Non-Goals

- Changing nudge logic or conditions
- Modifying nudge TTL behavior
- Adding new nudge conditions

## Design

### New Hook Structure

`hooks/stop-handler.py`:
```python
#!/usr/bin/env python3
"""
Unified Stop Handler — consolidates stop-guard, stop-pipeline-guard, compact-hint
"""

import subprocess
import json
import os
from datetime import datetime, timedelta

def get_git_status():
    """Single git status call, cached for all checks."""
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def get_git_log():
    """Single git log call for nudge conditions."""
    result = subprocess.run(
        ["git", "log", "--oneline", "-10"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def check_nudges(git_status, git_log):
    """
    Combined nudge checks — all conditions evaluated once.
    Returns list of nudge messages.
    """
    nudges = []
    
    # Nudge 1: Uncommitted changes
    if git_status:
        nudges.append(f"Uncommitted changes detected:\n{git_status}")
    
    # Nudge 2: Pipeline status (from stop-pipeline-guard)
    pipeline_status = check_pipeline_status(git_log)
    if pipeline_status:
        nudges.append(pipeline_status)
    
    # Nudge 3: Compact hint (from compact-hint)
    compact_hint = check_compact_hint(git_status)
    if compact_hint:
        nudges.append(compact_hint)
    
    return nudges

def check_pipeline_status(git_log):
    """Check if pipeline is in valid state."""
    # Logic from stop-pipeline-guard.py
    # ...
    return None

def check_compact_hint(git_status):
    """Suggest git gc if repo is large."""
    # Logic from compact-hint.py
    # ...
    return None

def write_log(nudges):
    """Single log entry for all nudges."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "nudges_count": len(nudges),
        "nudges": nudges
    }
    # Append to .zie/hooks.log or similar
    with open(".zie/stop-handler.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    git_status = get_git_status()
    git_log = get_git_log()
    
    nudges = check_nudges(git_status, git_log)
    
    if nudges:
        for nudge in nudges:
            print(nudge)
        write_log(nudges)
        exit(1)  # Stop blocked
    
    exit(0)  # Stop allowed

if __name__ == "__main__":
    main()
```

### Hook Configuration Update

`hooks/hooks.json`:
```json
{
  "hooks": {
    "stop": [
      {
        "name": "stop-handler",
        "script": "hooks/stop-handler.py"
      }
    ]
  }
}
```

**Before:** 3 entries for stop-guard, stop-pipeline-guard, compact-hint
**After:** 1 entry for stop-handler

### Files to Delete

After merge is complete and tested:
- `hooks/stop-guard.py`
- `hooks/stop-pipeline-guard.py`
- `hooks/compact-hint.py`

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `hooks/stop-handler.py` | New | Unified Stop handler |
| `hooks/hooks.json` | Modify | Single hook entry |
| `hooks/stop-guard.py` | Delete | Merged into stop-handler |
| `hooks/stop-pipeline-guard.py` | Delete | Merged into stop-handler |
| `hooks/compact-hint.py` | Delete | Merged into stop-handler |

## Dependencies

- None (standalone hook consolidation)

## Testing Plan

1. **Unit**: Each nudge condition tested independently
2. **Integration**: Stop hook with uncommitted changes — verify nudge
3. **Integration**: Stop hook with pipeline issues — verify nudge
4. **Integration**: Clean stop — verify no nudges, exit 0
5. **Token audit**: Measure token savings vs baseline (3 hooks → 1)

## Rollout Plan

1. Create `stop-handler.py` with merged logic
2. Update `hooks.json` to use new handler only
3. Test all nudge conditions
4. Verify old hooks can be deleted
5. Delete old hook files

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Nudge logic regression | Copy logic exactly, add unit tests |
| Hook failure blocks Stop | Test thoroughly before deleting old hooks |
| Log format change | Preserve existing log format for compatibility |

## Open Questions

None — scope is well-defined.
