---
name: write-plan
description: Write a detailed implementation plan from an approved spec. Saves to zie-framework/plans/.
argument-hint: "<slug> [--no-memory]"
metadata:
  zie_memory_enabled: true
model: sonnet
effort: low
---

# write-plan — Spec → Implementation Plan

Write a comprehensive, task-by-task implementation plan. Output lives in `zie-framework/plans/`.

## Arguments

| Pos | Var | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Backlog slug — locates spec file `zie-framework/specs/YYYY-MM-DD-<slug>-design.md` | absent → prompt user or select from approved specs |
| 1 | `$ARGUMENTS[1]` | Flags string (e.g. `--no-memory` to skip zie-memory recall) | absent/empty → all defaults apply |

Parse flags by splitting on whitespace. Never block or error on missing arguments.

## เตรียม context

If `zie_memory_enabled=true`: → zie-memory: recall(project=`<project>`, domain=`<feature-area>`, tags=[plan, implementation], limit=10). Surface past plan patterns, pitfalls, and architectural decisions.

## Plan Document Header

Every plan MUST start with:

```markdown
---
approved: false
approved_at:
backlog: backlog/<slug>.md
---

# <Feature Name> — Implementation Plan

**Goal:** <one sentence>
**Architecture:** <2-3 sentences>
**Tech Stack:** <key technologies>
**Risk Review:** <1-2 sentences — key risks, rollback strategy, hidden dependencies>

---
```

## แผนที่ไฟล์

Before defining tasks, map out files to create or modify:

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `path/to/file.py` | What this file does |
| Modify | `path/to/existing.py` | What changes |

## Risk Review

Before writing tasks, explicitly consider:

1. **What can go wrong?** — Identify the top 2-3 failure modes (wrong assumptions, dependency failures, data loss).
2. **Rollback strategy** — How do you undo each change if it breaks in production? Is rollback safe?
3. **Hidden dependencies** — What other systems, files, or teams does this change affect that aren't obvious from the spec?
4. **Rejected alternatives** — What approaches were considered but dismissed? Why? (Helps future readers understand the decision.)

Add findings to the plan's `**Risk Review:**` header. If no significant risks: write "No significant risks identified."

## Task Sizing Guidance

| Size | Signals | Action |
| --- | --- | --- |
| Too big | Multiple files changed or unrelated behaviors | Split into 2+ tasks |
| Right | Single file/function, single behavior tested | Proceed |
| Too small | Only renaming or constant change | Merge with adjacent task |

Task count: S ≤3 · M 4–7 · L 8–15 (consider splitting) · ⚠️ >15 = split by feature boundary.

## โครงสร้าง Task

Each task follows TDD RED → GREEN → REFACTOR:

```markdown
## Task N: <Task Name>

<!-- depends_on: Task M -->

**Acceptance Criteria:**
- <observable behavior 1>
- <observable behavior 2>

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`

- [ ] **Step 1: Write failing tests (RED)**
  <exact test code>
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  <exact implementation>
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  <cleanup notes>
  Run: `make test-unit` — still PASS
```

Use `<!-- depends_on: Task N, Task M -->` for dependencies. Tasks without `depends_on` can run in parallel.

**File conflict check:** If multiple `depends_on: none` tasks write to the same file, add `<!-- depends_on: TN -->` to serialize them.

**Max parallel tasks: 4.** Group independent tasks into batches of 4; queue excess tasks.

## บันทึกไว้ที่

Save plan to: `zie-framework/plans/YYYY-MM-DD-<feature-slug>.md`

## Approval Gate — Caller Responsibility

> **reviewer-gate hook blocks any Write/Edit that sets `approved: true`.** This skill writes `approved: false` only. Approval is handled by the caller.

The caller (`/plan` or `/sprint`) must:
1. Run the reviewer skill after this skill finishes.
2. Set approval via Bash (never via Write/Edit):
   ```bash
   python3 hooks/approve.py zie-framework/plans/YYYY-MM-DD-<slug>.md
   ```

Never write/edit `approved: true` — the hook will block it.
