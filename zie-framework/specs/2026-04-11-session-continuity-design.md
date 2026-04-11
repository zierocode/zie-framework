---
approved: false
approved_at:
backlog:
---

# Session Continuity — Design Spec

**Problem:** Every new session starts cold. Zie must manually remember where they left off — which branch, which feature was in progress, which tests were failing — before they can continue working.

**Approach:** Extend SessionStart hook to read `.remember/now.md`, current git branch + status, and last test results, then surface a structured "where you left off" summary at session start.

**Components:**
- `hooks/session-resume.py` — extend with continuity snapshot display
- Reads: `.remember/now.md`, `git status`, `git branch`, last test result cache if present

**Data Flow:**
1. Read `.remember/now.md` (WIP buffer) — extract last active feature/task
2. Run `git status --short` + `git branch --show-current` — detect branch + uncommitted changes
3. Check for last test result: `/tmp/zie-<project>-last-test-result` (written by auto-test hook)
4. If WIP found → display continuity snapshot:

```
[zie-framework] Last session
  Feature:  conversation-capture (in progress)
  Branch:   dev — 3 uncommitted files
  Tests:    2 failing (test_design_tracker, test_handoff_write)
  Next:     /implement or run make test-fast to resume
```

5. If no WIP found → skip (don't show empty snapshot)
6. If zie-framework/ not initialized → show init prompt (Area 4 behavior, not continuity)

**Error Handling:**
- `.remember/now.md` missing: skip continuity display silently
- git commands fail (not a git repo): skip git state, show only memory buffer
- Test result cache missing: omit test line from snapshot
- Never blocks session start — all reads are best-effort

**Testing:**
- Unit: snapshot displayed when `.remember/now.md` has content
- Unit: snapshot omitted when no WIP found
- Unit: git failure handled gracefully, exits 0
- Unit: exits 0 on malformed event (@pytest.mark.error_path)
