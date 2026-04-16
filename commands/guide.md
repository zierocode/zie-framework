---
description: Framework walkthrough — show current pipeline state and recommend next 1-3 actions.
argument-hint: ""
allowed-tools: Read, Glob, Grep, Bash
model: sonnet
effort: low
---

# /guide — Framework Walkthrough

On-demand orientation: understand zie-framework capabilities, see where you
are in the pipeline, and get concrete recommended next actions.

<!-- preflight: minimal -->

## Step 1 — Check framework presence

Check whether `zie-framework/` exists in the current working directory.

**If absent:**

```
zie-framework is not initialized in this project.

zie-framework is a solo developer SDLC framework for Claude Code. It provides
a structured spec-first, TDD pipeline with automated hooks for intent detection,
context injection, and quality gates.

To get started: run `/init` to bootstrap zie-framework in this project.
After /init, run `/guide` again for a full walkthrough.
```

Stop here.

## Step 2 — Read current state

1. Read `zie-framework/ROADMAP.md` (if present):
   - Now lane items → active feature
   - Next lane items → pending work
2. Scan `zie-framework/specs/` for files matching `*-<item-slug>-design.md`:
   - Read YAML frontmatter — check `approved: true`
3. Scan `zie-framework/plans/` for files matching `*-<item-slug>.md`:
   - Read YAML frontmatter — check `approved: true`
4. If ROADMAP.md missing: skip pipeline position check; show command list only.

## Step 3 — Show command overview

Print the framework command map:

```
## zie-framework Commands

| Command | Purpose |
|---------|---------|
| /backlog | Capture a new idea |
| /spec | Design a backlog item |
| /plan | Plan implementation from approved spec |
| /implement | TDD implementation (agent mode required) |
| /sprint | Full pipeline in one go |
| /fix | Debug and fix failing tests or broken features |
| /chore | Maintenance task, no spec needed |
| /hotfix | Emergency fix, ship fast |
| /status | Show current SDLC state |
| /audit | Project audit |
| /retro | Post-release retrospective |
| /release | Merge dev→main, version bump |
| /resync | Refresh project knowledge |
| /init | Bootstrap zie-framework in a new project |

Workflow: backlog → spec (reviewer) → plan (reviewer) → implement → release → retro
Use /sprint to run the full pipeline in one session.
```

## Step 4 — Show active work

If Now lane has items:

```
## Active Feature
<feature name from Now lane>
```

If Now lane is empty: skip.

## Step 5 — Determine pipeline position and recommend next actions

For each Next-lane item, determine its state:

| State | Condition | Recommended action |
|-------|-----------|-------------------|
| no-spec | No `*<item-slug>-design.md` in specs/ | `/spec <item>` |
| spec-unapproved | Spec file exists but `approved: true` absent | Run `Skill('spec-review')` then `python3 hooks/approve.py <spec-path>` |
| spec-approved-no-plan | Approved spec but no plan file | `/plan <item>` |
| plan-approved | Both spec + plan approved | `/implement` or `/sprint <item>` |

Print recommended next 1-3 actions with exact commands.

**Example output when Next lane has items without approved specs:**

```
## Recommended Next Actions

1. **Design** — run `/spec my-feature` to write the design spec
2. **Review** — after writing spec, run `Skill('spec-review')` to validate
3. **Plan** — once approved, run `/plan my-feature`
```

**Example when all Next items have approved spec + plan:**

```
## Ready to Implement

All backlog items have approved specs and plans.
Run `/implement` to start TDD implementation, or `/sprint` for the full pipeline.
```

## Error Handling

- ROADMAP.md missing: skip pipeline position, show command list only (no crash)
- specs/ or plans/ missing: treat all items as no-spec state
- File read errors: skip that item, continue with remaining

→ /backlog to start a new item
