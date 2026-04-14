---
approved: true
spec: specs/2026-04-14-stop-handler-merge-design.md
---

# Implementation Plan: Stop Handler Merge

## Overview

Consolidate 3 sequential Stop hooks (stop-guard, stop-pipeline-guard, compact-hint) into a single `stop-handler.py` with unified logic: one git status call, combined nudge checks, single log entry.

## Tasks

### Phase 1: Create Unified Handler

1. **Create `hooks/stop-handler.py`**
   - Implement unified Stop handler:
     ```python
     def get_git_status() -> str
     def get_git_log() -> str
     def check_nudges(git_status, git_log) -> list[str]
     def check_pipeline_status(git_log) -> Optional[str]
     def check_compact_hint(git_status) -> Optional[str]
     def write_log(nudges: list)
     def main()
     ```
   - Single `git status --short` call (shared across all checks)
   - Single `git log --oneline -10` call
   - Combined nudge evaluation in single pass
   - Single log entry with all nudges

2. **Copy nudge logic from existing hooks**
   - From `stop-guard.py`: uncommitted changes nudge
   - From `stop-pipeline-guard.py`: pipeline status check
   - From `compact-hint.py`: compact hint check
   - Preserve exact logic (no changes to nudge conditions)

### Phase 2: Update Hook Configuration

3. **Update `hooks/hooks.json`**
   - Replace 3 stop hook entries with 1:
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

### Phase 3: Testing

4. **Unit tests**
   - Test each nudge condition independently
   - Test combined nudge evaluation
   - Test log format preservation

5. **Integration tests**
   - Stop with uncommitted changes → verify nudge
   - Stop with pipeline issues → verify nudge
   - Stop with both → verify both nudges
   - Clean stop → verify no nudges, exit 0

6. **Token audit**
   - Measure token savings (3 hooks → 1)
   - Verify git status calls reduced (3 → 1)

### Phase 4: Cleanup

7. **Delete old hook files**
   - `hooks/stop-guard.py`
   - `hooks/stop-pipeline-guard.py`
   - `hooks/compact-hint.py`

## Acceptance Criteria

- [ ] Single `stop-handler.py` implemented
- [ ] All 3 nudge conditions preserved
- [ ] One git status call per Stop event
- [ ] Combined nudge checks in single pass
- [ ] Single log entry with all nudges
- [ ] Old hook files deleted
- [ ] All tests passing
- [ ] Token savings verified (~600 tokens per Stop)

## Estimated Effort

- Phase 1: ~2 hours
- Phase 2: ~30 min
- Phase 3: ~1.5 hours
- Phase 4: ~30 min
- **Total: ~4.5 hours**
