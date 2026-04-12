---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-observability-health-command.md
---

# Lean Observability: Framework Health Section in /status — Design Spec

**Problem:** `/status` exposes SDLC state (ROADMAP lanes, test health, knowledge
sync) but has no visibility into framework health: hook stop-failure history,
drift-log bypass count, active config settings, and optional dependency status
(zie-memory, playwright). Hook stderr errors go silently to stderr and are never
aggregated, meaning silent hook failures are only discoverable by manually
grepping `/tmp` or session logs.

**Approach:** Add a "Framework Health" section to the existing `/status` command
output (Step 7 print block). Read four lightweight file/config sources — no
new hooks, no new log files. Surface the last 5 entries from the stopfailure-log
(`/tmp/zie-<project>-failure-log`), the drift count from `zie-framework/.drift-log`
(already read in Step 2), `safety_check_mode` from `.config` (already loaded in
Step 2), and `zie_memory_enabled` / `playwright_enabled` from `.config`. All
reads are best-effort: missing file → friendly "no entries" message, never error.

**Components:**

- `commands/status.md` — add Framework Health section to Step 2 (read list) and
  Step 7 (print block); no new commands or hooks
- `tests/test_commands_status.py` — new test file asserting Framework Health
  section renders correctly with and without stopfailure-log entries
- `zie-framework/specs/2026-04-04-lean-observability-health-command-design.md`
  — this file

**Data Flow:**

1. `/status` Step 2 reads `zie-framework/.config` → extracts `safety_check_mode`,
   `zie_memory_enabled`, `playwright_enabled` (already happens today — just needs
   to surface them in output)
2. `/status` Step 2 reads drift count from `zie-framework/.drift-log` (already
   happens today — count exposed in Drift row)
3. `/status` Step 7 reads stopfailure-log at
   `project_tmp_path("failure-log", safe_project_name(cwd.name))` — uses same
   path logic as `stopfailure-log.py`:
   - `/tmp/zie-<sanitized-project-name>-failure-log`
   - If file missing → show "No stop failures recorded"
   - If present → tail last 5 non-empty lines, format as timestamped list
4. `/status` Step 7 renders new **Framework Health** section below the Tests
   table, before the "Next step" suggestion

**Output format (appended to Step 7 print block):**

```
**Framework Health**

| | |
| --- | --- |
| safety_check_mode | regex |
| zie-memory | enabled / disabled |
| playwright | enabled (v1.x.x) / disabled |
| Drift bypasses | N events |

**Stop failures (last 5):**
- [2026-04-04T10:00:00Z] error_type=rate_limit wip=my-feature
- No stop failures recorded
```

**Edge Cases:**

- Stopfailure-log file missing (new project, no failures yet) → "No stop
  failures recorded" — never fail or error
- Stopfailure-log has > 5 entries → show only last 5 (tail)
- Stopfailure-log line truncation → clip at 120 chars per line to stay within
  markdownlint MD013 limit
- `playwright_enabled=true` in config but `playwright` CLI not on PATH →
  show "enabled (version unknown)" — do not shell out to check version since
  `/status` must remain fast and network-free
- `.config` missing → all config values show as defaults (already handled by
  `load_config()`)
- `zie-framework/` dir missing → Step 1 initialization check already exits
  early — Framework Health section is never reached

**Out of Scope:**

- Aggregating hook stderr output into a structured log (separate effort)
- Playwright version detection via subprocess (adds latency; YAGNI for now)
- Session-learn output surfacing (session-learn log not currently written to a
  stable path — separate effort)
- Subagent-stop log summary (subagent-stop log in `/tmp` — lower value for
  daily use; can be added later)
- A standalone `/health` command (the backlog item scopes this as a section in
  `/status`; a separate command is YAGNI)
- Historical trend or time-series of stop failures
