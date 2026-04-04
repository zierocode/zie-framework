---
description: Chore track — maintenance tasks with no spec required
argument-hint: "<description>"
allowed-tools: Read, Edit, Write, Bash, Glob, Grep
---

# /zie-chore — Chore Track

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

4. **Commit** — `git add -A && git commit -m "chore: <slug>"`

5. **Done** — print:
   ```
   Chore complete: <slug>
   ROADMAP Done entry added.
   Next: /zie-status
   ```

## Notes

- No spec, no plan, no drift log required.
- Chores go directly to Done — they bypass the Now/Ready lanes.
- If the chore reveals a real feature need → `/zie-backlog` to capture it.
- Keep chores small. If it needs a spec → use the standard pipeline instead.
