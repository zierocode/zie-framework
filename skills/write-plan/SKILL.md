---
name: write-plan
description: Write a detailed implementation plan from an approved spec. Saves to zie-framework/plans/.
metadata:
  zie_memory_enabled: true
---

# write-plan — Spec → Implementation Plan

Write a comprehensive, task-by-task implementation plan. Output lives in
`zie-framework/plans/`.

## เตรียม context

If `zie_memory_enabled=true`:

- `recall project=<project> domain=<feature-area> tags=[plan, implementation]
  limit=10`
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

## Context from brain

_Prior memories relevant to this feature are surfaced here by /zie-plan before
handing off to /zie-implement._

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
