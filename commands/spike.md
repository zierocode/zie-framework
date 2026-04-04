---
description: Spike track — time-boxed exploration in an isolated sandbox directory
argument-hint: "<slug>"
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, WebSearch, WebFetch
---

# /spike — Spike Track

A time-boxed investigation or proof-of-concept. Work lives in `spike-<slug>/`
and does not write to ROADMAP or produce a shippable artifact.

## ตรวจสอบก่อนเริ่ม

1. Derive slug from argument or ask: "What are you investigating? (one-line slug)"
   `slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')`

## Steps

1. **Create sandbox** — `mkdir spike-<slug>/` at repo root. All spike files live here.

2. **Define the question** — state clearly:
   - What are you trying to learn?
   - What is the time box? (default: 2 hours)
   - What does "done" look like?

3. **Investigate** — explore, prototype, benchmark. Write findings to
   `spike-<slug>/FINDINGS.md`.

4. **Summarize** — in `spike-<slug>/FINDINGS.md`:
   - Answer the original question.
   - Recommendation: proceed / abandon / revisit.
   - If proceeding → `/backlog` to capture as a real backlog item.

5. **Done** — print:
   ```
   Spike complete: spike-<slug>/FINDINGS.md
   Next: /backlog "<slug>" to promote, or discard spike-<slug>/ if abandoned.
   ```

## Notes

- Spike does not write to ROADMAP, spec, or plan files.
- `spike-<slug>/` directory is the only output.
- No drift log entry needed — spikes are exploratory, not pipeline bypasses.
- Promote findings via `/backlog` if the spike validates an approach.
