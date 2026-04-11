---
approved: false
approved_at:
backlog:
---

# Observability / Health Command — Design Spec

**Problem:** Hooks fail silently. There is no way to know which hooks are firing, which are erroring, or whether the framework is healthy without reading raw log files manually.

**Approach:** `/health` command aggregates existing log files in `/tmp/zie-*` and displays a structured health report: hook status, recent errors, config validation, session summary.

**Components:**
- `commands/health.md` — new `/health` command
- Reads: `/tmp/zie-<project>-subagent-log`, `/tmp/zie-<project>-session-*`, hook error output in stderr logs

**Data Flow:**
1. Read subagent log → count agent completions, last run timestamps
2. Read session context cache → detect active session state
3. Scan for recent hook stderr output (last 24h) → surface any errors
4. Validate config: check `hooks/hooks.json` entries exist on disk
5. Display report:

```
zie-framework health — <project>

Hooks
  [✅] intent-classify       last fired: 2m ago
  [✅] reviewer-gate         last fired: 14m ago
  [⚠️] brainstorm-detect     no recent activity
  [❌] design-tracker        error: FileNotFoundError (see log)

Session
  Active: yes — context cache present
  Subagents completed this session: 3

Config
  [✅] All hook scripts found on disk
  [✅] hooks.json valid JSON
```

**Error Handling:**
- Log file missing: show "no data" for that hook — never abort
- Config validation error: show clearly in report
- `/health` always exits cleanly — read-only command, no side effects

**Testing:**
- Unit: health report shows ✅ when logs present and clean
- Unit: health report shows ❌ when hook log contains error
- Unit: health report handles missing log files gracefully
- Unit: config validation detects missing hook script on disk
