---
approved: true
spec: specs/2026-04-14-pre-computed-version-design.md
---

# Pre-Computed Version Suggestion — Implementation Plan

## Overview

Compute version suggestion at sprint start, store in `.zie/sprint-state.json`, reuse at release to eliminate redundant git log scans.

## Tasks

### Phase 1: Sprint State Schema Update

1. **Update sprint-state.json schema docs**
   - Add `version_suggestion` object schema to session-state documentation
   - Document fields: `current`, `suggested`, `bump_type`, `reason`, `computed_at`

### Phase 2: Version Computation Logic

2. **Create version computation module**
   - File: `hooks/version_compute.py`
   - Functions:
     - `get_current_version()` — read VERSION file
     - `get_commits_since_release(version)` — git log since last tag
     - `analyze_commits(commits)` — detect breaking/features/fixes
     - `compute_suggested_version(current, commits)` — semver logic
     - `compute_version_suggestion()` — main entry point

### Phase 3: Sprint Integration

3. **Update `commands/sprint.md`**
   - Phase 1: Call `version_compute.py` after sprint state initialized
   - Write `version_suggestion` to `.zie/sprint-state.json`
   - Display suggestion to user

### Phase 4: Release Gate Integration

4. **Update `commands/release.md`**
   - Read `version_suggestion` from `.zie/sprint-state.json`
   - Display suggestion if available
   - Fallback: compute on-demand if state missing

### Phase 5: Testing

5. **Unit tests**
   - `test_version_compute.py`:
     - `test_get_current_version()`
     - `test_analyze_commits_breaking()`
     - `test_analyze_commits_features()`
     - `test_compute_suggested_version_minor()`
     - `test_compute_suggested_version_patch()`
     - `test_compute_suggested_version_major()`

6. **Integration tests**
   - Sprint start → verify `version_suggestion` in state
   - Release gate → reads from state correctly
   - Edge case: no commits → patch bump

## Acceptance Criteria

- [ ] Git log scanned once at sprint start
- [ ] Release reads from state, no git log scan
- [ ] Version suggestion schema stored correctly
- [ ] Fallback works when state missing
- [ ] All unit tests pass
- [ ] Integration tests pass

## Dependencies

- None (uses existing git + file I/O)

## Rollout

1. Create `hooks/version_compute.py` + tests
2. Update `commands/sprint.md` to compute + store
3. Update `commands/release.md` to read from state
4. Test with fresh sprint → release cycle
