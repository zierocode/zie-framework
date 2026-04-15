---
approved: true
spec: specs/2026-04-14-combined-nudge-checks-design.md
---

# Combined Nudge Checks — Implementation Plan

## Overview

Consolidate 3 nudge conditions into single git log pass within `stop-handler.py`. Parse once, distribute to all nudge checks.

## Tasks

### Phase 1: Git Log Parser

1. **Create combined git log parser**
   - File: `hooks/stop-handler.py` (modify existing)
   - Function: `get_git_log_parsed(limit=50)`
   - Returns: list of `{hash, message}` dicts
   - Single subprocess call to `git log --oneline -50`

### Phase 2: Nudge Check Functions

2. **Refactor nudge conditions**
   - `check_nudges(git_status, commits)` — main entry point
   - `check_pipeline_from_commits(commits)` — WIP detection
   - `check_stale_branch_from_commits(commits)` — no recent commits
   - `check_uncommitted_changes(git_status)` — status nudge

### Phase 3: Stop Handler Integration

3. **Update `hooks/stop-handler.py`**
   - Replace 3× `git log` calls with single `get_git_log_parsed()`
   - Pass parsed commits to all nudge check functions
   - Consolidate nudge output

### Phase 4: Testing

4. **Unit tests**
   - `test_stop_handler.py`:
     - `test_git_log_parsing()`
     - `test_check_pipeline_wip_detection()`
     - `test_check_stale_branch_no_commits()`
     - `test_combined_nudges_single_call()`

5. **Integration tests**
   - Verify all 3 nudge conditions fire correctly
   - Token audit: measure savings vs 3× git log

## Acceptance Criteria

- [ ] Single git log call per Stop event
- [ ] All 3 nudge conditions work correctly
- [ ] Token usage reduced (measure before/after)
- [ ] No nudge functionality lost

## Dependencies

- `stop-handler-merge` (provides stop-handler.py structure)

## Rollout

1. Add `get_git_log_parsed()` to stop-handler.py
2. Refactor nudge checks to use parsed commits
3. Test each nudge condition independently
4. Measure token savings
