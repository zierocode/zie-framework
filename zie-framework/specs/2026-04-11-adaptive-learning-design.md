---
approved: false
approved_at:
backlog:
---

# Adaptive Learning — Design Spec

**Problem:** Framework hints and recommendations are static — they don't account for Zie's actual working patterns. Commands used frequently, steps skipped consistently, and personal workflow preferences are invisible to the framework, causing irrelevant hints.

**Approach:** Stop hook records per-session behavioral signals to a pattern log. After N sessions, intent-classify.py and hint injection read the aggregate to personalize scoring thresholds and recommendations.

**Components:**
- `hooks/subagent-stop.py` — extend to append behavioral record to pattern log
- `hooks/intent-classify.py` — extend to read pattern aggregate and adjust thresholds
- Pattern log: `/tmp/zie-<project>-pattern-log.jsonl`
- Pattern aggregate: `/tmp/zie-<project>-pattern-aggregate.json` (rebuilt every 10 sessions)

**Data Flow:**

*A — Recording (Stop hook extension):*
At session end, append one record to pattern log:
```json
{
  "ts": "ISO timestamp",
  "commands_used": ["/spec", "/plan", "/implement"],
  "steps_skipped": ["retro"],
  "session_duration_mins": 45,
  "intent_hints_acted_on": ["sprint"],
  "intent_hints_ignored": ["brainstorm"]
}
```

*B — Aggregate rebuild (every 10 sessions):*
Read last 30 records → compute:
```json
{
  "most_used_commands": ["/implement", "/fix", "/spec"],
  "frequently_skipped": ["retro", "chore"],
  "hint_acceptance_rate": {"sprint": 0.8, "brainstorm": 0.3},
  "avg_session_duration_mins": 38
}
```
Write to pattern aggregate file.

*C — Personalized hints (intent-classify.py):*
1. Read pattern aggregate at hook start (cached in memory for session)
2. Adjust scoring:
   - If `hint_acceptance_rate["brainstorm"] < 0.3` → raise brainstorm threshold (less aggressive)
   - If `hint_acceptance_rate["sprint"] > 0.7` → lower sprint threshold (more responsive)
3. Skip hints for commands in `frequently_skipped` (Zie knows they're optional)

**Privacy:** All data stays local in `/tmp/` — never sent anywhere. Cleared when OS clears `/tmp/`.

**Error Handling:**
- Pattern log write fails: skip silently, continue session normally
- Pattern aggregate missing: use default thresholds (existing behavior)
- Corrupt aggregate: delete and rebuild from log on next session
- Tier 1 outer guard on all extensions: bare except → exit 0

**Testing:**
- Unit: session record written with correct fields
- Unit: aggregate rebuilt correctly after 10 sessions
- Unit: intent thresholds adjusted based on acceptance rates
- Unit: missing aggregate falls back to defaults
- Unit: corrupt aggregate deleted and rebuilt gracefully
- Unit: exits 0 on pattern log write failure (@pytest.mark.error_path)
