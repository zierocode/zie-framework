---
description: Display hook health, session state, and config validation — read-only diagnostic command.
argument-hint: ""
allowed-tools: Read, Glob, Grep, Bash
model: sonnet
effort: low
---

# /health — Framework Health Report

Read-only diagnostic — never modifies state. Shows hook status, session
state, and config validation in a single glance.

<!-- preflight: minimal -->

## Steps

1. **Check prerequisites**
   - If `zie-framework/` absent → print "Not initialized — run /init first." Stop.

2. **Validate hooks.json config**
   - Read `hooks/hooks.json` — verify valid JSON
   - For each hook command entry: check that the referenced `.py` file exists on disk
   - Record: `[✅]` if found, `[❌ missing]` if not

3. **Check recent hook activity**
   - Scan `/tmp/zie-<project>-*` flags for timestamps using `ls -la`
   - Map flag names to hook names:
     - `session-context-*` → subagent-context (active session)
     - `last-test` → auto-test (last test run)
     - `intent-sprint-flag` → intent-sdlc (sprint detected)
     - `design-mode` → design-tracker (design conversation active)
   - Compute age of each flag

4. **Read session state**
   - Check `zie-framework/.config` — show enabled features (zie_memory, playwright)
   - Check if roadmap cache is fresh

5. **Print health report**

   ```
   zie-framework health — <project>

   Config
     [✅] hooks.json valid JSON
     [✅] All 14 hook scripts found on disk

   Hook Activity (this session)
     [✅] intent-sdlc        last signal: 3m ago
     [✅] subagent-context   session cache: active
     [✅] auto-test          last run: 12m ago
     [⬜] design-tracker     no activity this session

   Session State
     Branch:   dev
     Features: zie_memory=disabled, playwright=disabled
     Roadmap:  cache fresh (hit 2m ago)

   Pipeline
     Active: <slug or "none">
     ROADMAP: <Now lane summary>
   ```

6. **Config warnings**
   - Missing hook script on disk → `[❌] <hook>.py — script not found at <path>`
   - Invalid JSON in hooks.json → `[❌] hooks.json — JSON parse error`
   - Show each warning clearly but continue report

## Error Handling

- `/tmp` unreadable: skip hook activity section, show "unavailable"
- Config file missing: show defaults assumed
- Git command fails: skip branch info
- Always exits cleanly — never halts or modifies anything

→ /status for current project state
