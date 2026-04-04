---
description: Chore track — maintenance tasks with no spec required
argument-hint: "<description>"
allowed-tools: Read, Edit, Write, Bash, Glob, Grep
---

# /chore — Chore Track

A lightweight track for maintenance work: dependency updates, config changes,
cleanup, tooling fixes. No spec required. A Done entry is added when complete.

## ตรวจสอบก่อนเริ่ม

1. Derive slug from argument or ask: "What is the chore? (one-line description)"
   `slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')`

## Steps

1. **Define the chore** — one sentence: what needs doing and why.

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

