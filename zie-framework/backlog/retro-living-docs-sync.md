# Retro Living Docs Sync

## Problem

After a release, `CLAUDE.md` and `README.md` often drift from the actual
codebase. The `/zie-release` docs gate only catches obvious cases (files that
changed in the current diff) and relies on Claude's judgment rather than
systematic extraction. `/zie-retro` updates `project/components.md` and
`project/architecture.md` but never touches `CLAUDE.md` or `README.md`
directly.

## Motivation

Project knowledge files are the first thing any context reads. Stale docs
cause Claude to make wrong assumptions about project structure, commands, and
tech stack — compounding across every session. The fix belongs in `/zie-retro`
where the full picture is available after a sprint ends.

## Rough Scope

- In `/zie-retro`: add a step that reads `CLAUDE.md` + `README.md`, extracts
  current codebase state (commands, hooks, skills, tech stack), and updates
  any gaps found
- Option A: integrate into existing "อัปเดต project knowledge" step in retro
- Option B: auto-trigger `/zie-resync` as the final step of retro
- Make the update systematic (compare actual vs. documented) not
  judgment-based
- Out of scope: real-time doc updates during implement (too noisy)
