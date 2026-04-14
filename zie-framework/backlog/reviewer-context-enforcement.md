---
tags: [chore]
---

# Reviewer Context Bundle Enforcement — remove disk fallback

## Problem

Fast-path exists but optional; disk fallback code paths remain; callers inconsistent with context_bundle passing. Dead code bloat (~300w across 3 skills); reviewers re-read when bundle missing.

## Motivation

Make context_bundle required; remove disk fallback; add validation error if missing. ~1.2w tokens saved per reviewer invocation.

## Rough Scope

**In:**
- `skills/plan-reviewer/SKILL.md` — make context_bundle required
- `skills/impl-reviewer/SKILL.md` — remove disk fallback
- `skills/spec-reviewer/SKILL.md` — remove disk fallback
- Add validation error if missing

**Out:**
- Reviewer logic (unchanged)

<!-- priority: MEDIUM -->
<!-- depends_on: unified-context-cache -->
