---
name: write-plan
description: Write a detailed implementation plan from an approved spec. Saves to zie-framework/plans/.
argument-hint: "<slug> [--no-memory]"
metadata:
  zie_memory_enabled: true
model: sonnet
effort: medium
---

# write-plan — Spec → Implementation Plan

Write a comprehensive, task-by-task implementation plan. Output lives in
`zie-framework/plans/`.

## Arguments

| Position | Variable | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Backlog slug — used to locate the spec file (`zie-framework/specs/YYYY-MM-DD-<slug>-design.md`) | absent → prompt user for slug |
| 1 | `$ARGUMENTS[1]` | Optional flags string (e.g. `--no-memory` to skip zie-memory recall) | absent/empty → all defaults apply |

When `$ARGUMENTS[0]` is absent, prompt the user to provide the slug or select
from the approved specs in `zie-framework/specs/`. Never block or error.

When `$ARGUMENTS[1]` is absent or empty, treat as no flags — all default
behaviour applies. Parse flags by splitting on whitespace and checking for
known flag names.

## เตรียม context

If `zie_memory_enabled=true`:

- Call `mcp__plugin_zie-memory_zie-memory__recall`
  with `project=<project> domain=<feature-area> tags=[plan, implementation] limit=10`
- Surface past plan patterns, known pitfalls, and relevant architectural
  decisions.

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

---
```

## แผนที่ไฟล์

Before defining tasks, map out which files will be created or modified:

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `path/to/file.py` | What this file does |
| Modify | `path/to/existing.py` | What changes |

## Task Sizing Guidance

**Right-size tasks before writing them:**

| Size | Description | Signals |
| --- | --- | --- |
| Too big | More than one file changed, or multiple unrelated behaviors | Split into 2+ tasks |
| Right | Single file/function changed, single behavior tested | Proceed |
| Too small | Only renaming or constant change | Merge with adjacent task |

**Task count guidance:**
- S plan: ≤3 tasks (single-session feature)
- M plan: 4–7 tasks (multi-session, one sprint)
- L plan: 8–15 tasks (multi-sprint — consider splitting)
- ⚠️ >15 tasks: plan is too large — split by feature boundary

**File conflict check:** Before assigning tasks, verify no two independent tasks write to the same output file. If they do, add `<!-- depends_on: TN -->` to serialize them.

## โครงสร้าง Task

Each task follows TDD RED → GREEN → REFACTOR:

```markdown
## Task N: <Task Name>

<!-- depends_on: Task M -->

**Acceptance Criteria:**
- <observable behavior 1 — what the user/system can verify>
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

Use `<!-- depends_on: Task N, Task M -->` to express task dependencies. Tasks
without depends_on can run in parallel.

**File conflict check:** Before assigning `depends_on: none` to multiple tasks,
verify that no two tasks write to the same output file. If tasks share an output
file, add `<!-- depends_on: TN -->` to serialize them.

**Max parallel tasks: 4.** When many tasks are independent, group them into
batches of 4 for parallel execution. Queue excess tasks and start them as
slots become available.

## บันทึกไว้ที่

Save plan to: `zie-framework/plans/YYYY-MM-DD-<feature-slug>.md`

After saving, run the **plan reviewer loop**:

- Invoke `Skill(zie-framework:plan-reviewer)` with path to plan + path to spec
- If ❌ Issues Found → fix issues → re-invoke reviewer → repeat until ✅ APPROVED
- Max 3 iterations → surface to human

Then update `zie-framework/ROADMAP.md`:

- Add to "Ready" section: `- [ ] <feature name> —
  [plan](plans/YYYY-MM-DD-<feature-slug>.md) ✓ approved`
- Wait for explicit approval before marking `approved: true` in frontmatter

## Notes

- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
