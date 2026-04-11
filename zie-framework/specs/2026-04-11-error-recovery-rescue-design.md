---
approved: false
approved_at:
backlog:
---

# Error Recovery (`/rescue`) — Design Spec

**Problem:** When stuck mid-pipeline, there is no structured way to determine the current state and what to do next. Zie must manually inspect spec/plan files to figure out where they are.

**Approach:** `/rescue` command scans zie-framework/ artifacts to detect current pipeline position and prints a clear "you are here" diagnosis with the exact next action.

**Components:**
- `commands/rescue.md` — new `/rescue` command

**Data Flow:**

1. Scan `zie-framework/backlog/` — list items with status
2. Scan `zie-framework/specs/` — find specs with `approved: false` vs `approved: true`
3. Scan `zie-framework/plans/` — find plans with `approved: false` vs `approved: true`
4. Check git branch + uncommitted changes
5. Check sprint state file `/tmp/zie-<project>-sprint-state.json` if present
6. Determine pipeline position and print diagnosis:

```
/rescue — pipeline diagnosis

Feature: conversation-capture
Status:  STUCK

✅ backlog item: present
✅ spec:         approved (2026-04-11)
✅ plan:         approved (2026-04-11)
🔄 implement:    in progress — 2 tests failing
⬜ release:      pending
⬜ retro:        pending

→ Next: fix failing tests, then run /release
   Failing: test_design_tracker, test_handoff_write
   Run: make test-fast
```

7. If no active feature found → "No active pipeline detected. Run /brainstorm or /backlog to start."
8. If multiple features in progress → list all, ask which to rescue

**Error Handling:**
- Missing artifacts: skip that step in diagnosis, mark as unknown
- Git commands fail: omit git state from report
- Always exits cleanly — read-only, no side effects

**Testing:**
- Unit: correct diagnosis when spec approved but plan missing
- Unit: correct diagnosis when plan approved but implement in progress
- Unit: "no active pipeline" when backlog empty
- Unit: multiple in-progress features listed correctly
- Unit: git failure handled gracefully
