# Workflow Lean

## Problem

Three workflow friction points slow down common operations without adding value: (1) /zie-spec and /zie-plan are separate commands requiring two full approval loops, but spec→plan is almost always done in sequence making the split a UX tax rather than a useful boundary; (2) /zie-audit always spawns all 4 agents regardless of scope, making a quick security scan cost as much as a full audit; (3) /zie-init's approval loop for knowledge docs regenerates the entire bundle per iteration even when only one section needs revision.

## Motivation

Users who just want to check security findings shouldn't pay for structural + external research agents. Users who want to go from idea to implementation should be able to run one command instead of two with two confirmation pauses. These are workflow lean improvements — reduce the number of steps, commands, and round-trips without changing the quality of outputs.

## Rough Scope

**In Scope:**
- /zie-audit: add `--focus` flag (e.g., `/zie-audit --focus security`) — skip non-selected dimension agents; update Phase 2 to conditionally spawn only selected agents
- /zie-spec: add `--draft-plan` flag — after spec approved, auto-trigger plan drafting in same session without requiring a separate /zie-plan invocation; plan-reviewer runs, auto-approved on pass
- /zie-init knowledge scan loop: change from full-regenerate to section-targeted edit — ask "which section to revise?" and only re-run that section's agent

**Out of Scope:**
- Merging /zie-spec and /zie-plan into one permanent command (keep as separate commands for users who want the boundary)
- Changing what gets reviewed or the reviewer logic
