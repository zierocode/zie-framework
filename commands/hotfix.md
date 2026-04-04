---
description: Emergency fix track — describe → fix → ship without full pipeline
argument-hint: "<slug>"
allowed-tools: Read, Edit, Write, Bash, Glob, Grep
model: sonnet
effort: low
---

# /hotfix — Emergency Hotfix Track

A lightweight track for urgent production fixes that cannot wait for the full
backlog → spec → plan → implement pipeline. **Use only for production incidents requiring immediate release. Triggers release gate automatically. For non-urgent bugs, use /fix instead.**

Opens a drift log entry, applies the fix, closes the drift log, then ships.

## ตรวจสอบก่อนเริ่ม

1. Derive slug from argument or ask: "What is the hotfix for? (one-line slug)"
   `slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')`
2. Read `zie-framework/.config` if it exists.

## Steps

1. **Open drift log entry** — append NDJSON to `zie-framework/.drift-log`:
   ```json
   {"track": "hotfix", "slug": "<slug>", "opened_at": "<iso8601>", "closed_at": null}
   ```

2. **Describe the problem** — ask (or derive from argument):
   - What is broken?
   - What is the minimal fix?
   - Is a test needed?

3. **Fix** — implement the minimal change. If a test is warranted, write it first
   (RED → GREEN). No spec, no plan required.

4. **Close drift log entry** — update the open event: set `closed_at` to now.

5. **Ship** — run `/release` to merge and tag. If this is a patch fix,
   the version bump should be a patch increment.

6. **Done** — print:
   ```
   Hotfix complete: <slug>
   Drift log closed. Track: hotfix | Duration: <elapsed>
   Next: /status
   ```

