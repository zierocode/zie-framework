---
approved: true
backlog: backlog/pre-computed-version.md
---

# Pre-Computed Version Suggestion — Design Specification

## Summary

Compute suggested version at sprint start from git log, store in `.zie/sprint-state.json`, and reuse at release time to eliminate redundant git log scans.

## Problem Statement

Current state:
- Version bump scans git log at release time
- CHANGELOG draft reads git log again
- Git log scanned 2× per release
- Semver logic runs under time pressure at release gate

## Goals

| Goal | Success Metric |
|------|----------------|
| Compute version once | Git log scanned at sprint start only |
| Reuse at release | Release reads from state, no git log scan |
| Faster release gate | Release time reduced by eliminating git log scans |

## Non-Goals

- Changing version bump logic or semver rules
- Modifying CHANGELOG format
- Automated version bump (still manual approval)

## Design

### Sprint State Schema

`.zie/sprint-state.json` (extended):
```json
{
  "sprint_id": "2026-04-14",
  "started_at": "2026-04-14T09:00:00Z",
  "items_completed": [],
  "version_suggestion": {
    "current": "1.28.4",
    "suggested": "1.29.0",
    "bump_type": "minor",
    "reason": "5 features, 0 breaking changes",
    "computed_at": "2026-04-14T09:00:00Z"
  }
}
```

### Version Computation Logic

`commands/sprint.md` Phase 1 computes version:

```python
import subprocess
import re
from datetime import datetime

def compute_version_suggestion():
    """
    Scan git log since last release tag.
    Determine bump type: major (breaking), minor (features), patch (fixes).
    """
    # Get current version
    with open("VERSION") as f:
        current = f.read().strip()
    
    # Get commits since last release
    result = subprocess.run(
        ["git", "log", "--oneline", "--no-merges", "v" + current + "..HEAD"],
        capture_output=True,
        text=True
    )
    commits = result.stdout.strip().split("\n") if result.stdout.strip() else []
    
    # Analyze commits
    has_breaking = any("BREAKING" in c or "!" in c for c in commits)
    has_features = any(c.startswith("feat:") or c.startswith("feat(") for c in commits)
    
    # Determine bump type
    if has_breaking:
        bump_type = "major"
    elif has_features:
        bump_type = "minor"
    else:
        bump_type = "patch"
    
    # Compute suggested version
    major, minor, patch = map(int, current.split("."))
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    
    suggested = f"{major}.{minor}.{patch}"
    
    return {
        "current": current,
        "suggested": suggested,
        "bump_type": bump_type,
        "reason": f"{len(commits)} commits, {bump_type} bump",
        "computed_at": datetime.now().isoformat() + "Z"
    }
```

### Release Gate Update

`commands/release.md` reads from state:

```python
# Before: scan git log, compute version
# After: read from sprint-state.json

with open(".zie/sprint-state.json") as f:
    state = json.load(f)

version_suggestion = state.get("version_suggestion")
if version_suggestion:
    print(f"Suggested version: {version_suggestion['suggested']}")
    print(f"Bump type: {version_suggestion['bump_type']}")
    print(f"Reason: {version_suggestion['reason']}")
else:
    # Fallback: compute on-demand (shouldn't happen in normal flow)
    version_suggestion = compute_version_suggestion()
```

### File Changes

| File | Action | Purpose |
|------|--------|---------|
| `.zie/sprint-state.json` | Modify (runtime) | Store version suggestion |
| `commands/sprint.md` | Modify | Compute version at sprint start |
| `commands/release.md` | Modify | Read version from sprint state |

## Dependencies

- **sprint-context-passthrough**: Required (sprint-state.json pattern)

## Testing Plan

1. **Unit**: Version computation logic (major/minor/patch detection)
2. **Integration**: Sprint start — verify version_suggestion in state
3. **Integration**: Release gate — verify reads from state correctly
4. **Edge case**: No commits since last release — verify patch bump

## Rollout Plan

1. Add version computation to `sprint.md` Phase 1
2. Add version_suggestion to sprint-state.json schema
3. Update `release.md` to read from state
4. Test with fresh sprint
5. Verify release gate uses suggestion

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Wrong version suggestion | Still manual approval — user can override |
| Sprint-state.json missing | Fallback to on-demand computation |
| Stale suggestion | Re-compute if computed_at > 24h old |

## Open Questions

None — scope is well-defined.
