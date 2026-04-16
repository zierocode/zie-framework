---
description: Debug path — skip ideation, go straight to systematic bug investigation and fix. Supports --hotfix (emergency ship) and --chore (maintenance, no spec).
argument-hint: "[--hotfix|--chore] <description>"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: sonnet
effort: low
---

# /fix — Bug Fix Path

<!-- preflight: full -->

Fast path for fixing bugs. Skips brainstorming and planning — goes directly to
debugging, regression test, fix, and verify.

Supports two flags:
- `--hotfix`: Emergency production fix — describe, fix, ship. Triggers release automatically.
- `--chore`: Maintenance task — no spec required. Adds Done entry when complete.

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).

## Parse flags

Check `$ARGUMENTS` for `--hotfix` or `--chore`. Derive slug from remaining text (or ask).

---

### --hotfix track

A lightweight track for urgent production fixes that cannot wait for the full
backlog → spec → plan → implement pipeline. **Use only for production incidents
requiring immediate release. Triggers release gate automatically.**

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

---

### --chore track

A lightweight track for maintenance work: dependency updates, config changes,
cleanup, tooling fixes. No spec required. A Done entry is added when complete.

1. **Define the chore** — one sentence: what needs doing and why.
   Derive slug from argument or ask: "What is the chore? (one-line description)"
   `slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')`

2. **Do the work** — apply the change. Run `make lint` and `make test-unit`
   if code is touched.

3. **Done entry** — add to `zie-framework/ROADMAP.md` Done section:
   `- [x] chore: <slug> — <one-line description>`

4. **Commit** — stage only the files changed in this chore (no `git add -A`):
   ```bash
   git add <specific-files-changed>
   git commit -m "chore: <slug>"
   ```
   Verify only intended files are staged before committing.

5. **Done** — print:
   ```
   Chore complete: <slug>
   ROADMAP Done entry added.
   Next: /status
   ```

---

### Default track (bug fix)

If `zie_memory_enabled=true`:
- Call `mcp__plugin_zie-memory_zie-memory__recall`
  with `project=<project> domain=<domain> tags=[bug, build-learning] limit=10`
- → detect recurring patterns, surface known fragile areas

#### ทำความเข้าใจ bug

1. If bug description provided as argument → use it.
   If not → ask: "What's the bug? Paste error output or describe the behavior."

2. Invoke `Skill(zie-framework:debug)`. The skill handles reproduce → isolate → confirm.

#### เขียน regression test (RED)

1. Write failing test that captures the bug. Use naming convention:
   `test_should_not_<failure_description>` or
   `test_<feature>_when_<condition>_should_<result>`
   Run `make test-unit` — must FAIL before fix. Non-negotiable.

#### แก้ bug (GREEN)

1. Implement minimal fix targeting root cause.
   Run `make test-unit` — regression test must PASS, no new failures.

#### ยืนยันว่าแก้ถูกต้อง

1. Invoke `Skill(zie-framework:verify)` with `scope=tests-only`.

2. If `has_frontend=true` and bug is UI-related:
   - Start dev server and verify visually.

#### บันทึกและเรียนรู้

1. If bug was tracked in ROADMAP → move to Done. Otherwise no update.

2. If `zie_memory_enabled=true`:
   - Call `mcp__plugin_zie-memory_zie-memory__remember`
     with `"Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`

3. Print:

   ```text
   Bug fixed: <description>
   Root cause: <cause>
   Fix: <brief description>
   Pattern: <recurring|one-off>
   Regression test: <test name> ✓

   Run /release when ready to release.
   ```