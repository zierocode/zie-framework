---
approved: false
approved_at:
backlog:
---

# Sprint Reliability — Design Spec

**Problem:** `/sprint` can fail mid-pipeline with no recovery path. There is no record of which step failed, no way to resume, and restarting risks duplicating already-completed artifacts.

**Approach:** Two components — (A) Stop hook records sprint phase completion to a state file; (B) `/sprint` reads state file at start and offers resume instead of restart when partial progress exists.

**Components:**
- `hooks/subagent-stop.py` — extend to write sprint phase completion to state file
- `commands/sprint.md` — extend with partial state detection + resume offer
- Sprint state file: `/tmp/zie-<project>-sprint-state.json`

**Data Flow:**

*Sprint state file schema:*
```json
{
  "feature": "<name>",
  "started_at": "ISO timestamp",
  "phases": {
    "backlog": "done",
    "spec": "done",
    "plan": "done",
    "implement": "in_progress",
    "release": "pending",
    "retro": "pending"
  },
  "last_updated": "ISO timestamp"
}
```

*A — Stop hook writes phase completions:*
1. Detect sprint phase completion signals in last_assistant_message
2. Update state file with completed phase
3. On full sprint completion: delete state file (clean slate)

*B — /sprint resume logic:*
1. Check for existing sprint state file
2. If found and feature matches (or user confirms) → resume from last completed phase
3. Display: "Partial sprint found: spec ✅ plan ✅ implement 🔄 — resuming from implement"
4. If no state file → start fresh (existing behavior)

**Error Handling:**
- State file corrupt/invalid JSON: delete and start fresh, warn user
- Phase detection ambiguous: err on side of re-running phase (idempotent operations)
- State file write fails: log warning, continue sprint without state tracking
- Never blocks sprint execution

**Testing:**
- Unit: state file written with correct phases after each completion signal
- Unit: /sprint detects partial state and offers resume
- Unit: corrupt state file handled gracefully
- Unit: clean state file deleted on sprint completion
- Unit: exits 0 on state write failure (@pytest.mark.error_path)
