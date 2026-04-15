---
date: 2026-04-15
status: approved
slug: skill-manual-auto-inject
---

# Skill-Manual-Auto-Inject — Auto-Inject Skill Context by SDLC Phase

## Problem

Skills like `spec-reviewer`, `write-plan`, and `impl-reviewer` must be invoked manually via `Skill()`. During `/implement`, the reviewer skill should run automatically but users forget or skip it. The framework already injects `additionalContext` via `intent-sdlc.py` on `UserPromptSubmit` — we can reuse this mechanism to inject skill content when the active phase matches.

## Solution

Add a phase-to-skill mapping to `intent-sdlc.py`. When the hook detects an active SDLC stage (spec, plan, implement), it appends the corresponding skill's SKILL.md content to the `additionalContext` payload. Mapping is configurable in `.config` under `skill_auto_inject`.

## Rough Scope

- **In:** Extend `intent-sdlc.py` to read SKILL.md files for the active stage and inject them as `additionalContext`. Add `skill_auto_inject` config with phase-to-skill mapping and `enabled` flag. Define default mapping: `spec`→`spec-reviewer`, `plan`→`write-plan`, `implement`→`impl-reviewer`.
- **Out:** Removing manual `Skill()` invocation (keep as fallback). Injecting skills unrelated to current phase.

## Files Changed

| File | Action |
|------|--------|
| `hooks/intent-sdlc.py` | Modify — add skill content injection after context build |
| `hooks/utils_config.py` | Modify — add `skill_auto_inject` config defaults |
| `hooks/session-resume.py` | Modify — inject skill context on session start when stage known |