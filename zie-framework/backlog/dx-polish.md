# DX Polish

## Problem

Three usability gaps make zie-framework feel rough for new and returning users: (1) /zie-status shows file paths and lane contents but no visual indication of where in the pipeline a feature is — users must mentally parse ROADMAP sections; (2) when spec-reviewer or plan-reviewer hits the max 3-iteration limit, the error message stops but doesn't tell the user what to do next; (3) write-plan has no guidance on task granularity, leading users to create 20-task plans for simple features or 3-task plans for complex ones.

## Motivation

Framework tooling should feel like it's guiding the user, not just executing steps. These three gaps create moments where users feel lost or unsure — they need to know what to do next when something fails, how many tasks is "right" for this feature, and where they are in the overall journey. All three are low-effort, high-impact polish items that make the difference between a tool that feels professional and one that feels unfinished.

## Rough Scope

**In Scope:**
- /zie-status: add ASCII pipeline progress indicator showing current stage with checkmarks (e.g., `backlog ✓ → spec ✓ → plan ✓ → [implement ▶] → release → retro`)
- All reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer): add explicit "next steps" block when max iterations reached — tell user exactly which command to run and which file to edit
- write-plan SKILL.md: add task granularity guidance table (Simple 1–3 files → 2–3 tasks, Medium 5+ files → 5–7 tasks, Complex 10+ files → 8–12 tasks, max 15)
- plan-reviewer: flag plans with >15 tasks as oversized

**Out of Scope:**
- Visual/graphical UI components
- Interactive TUI or terminal progress bars
- Changing reviewer pass/fail thresholds
