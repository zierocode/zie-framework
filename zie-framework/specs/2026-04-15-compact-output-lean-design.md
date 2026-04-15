---
date: 2026-04-15
status: approved
slug: compact-output-lean
---

# Compact Output — Lean Token Reduction

## Problem

Hook output (`intent-sdlc`, `session-resume`) and command output (`/status`, `/next`) contain verbose labels, repeated prefixes, and unnecessary padding. Every token costs context budget — a 15-25% reduction is achievable without losing decision-relevant information.

## Solution

Compress output by: (1) replacing `[zie-framework]` prefix with `[zf]` on every line, (2) collapsing multi-line session-resume blocks into 2-3 compact lines with key:value pairs, (3) shortening verbose labels (`Active:` → `now:`, `Brain:` → `mem:`), (4) trimming the workflow/anti-patterns line to a one-line mnemonic, (5) removing decorative newlines/padding from `/status` tables, (6) compressing the `/status` pipeline row to inline arrows.

## Rough Scope

**In:**
- `hooks/intent-sdlc.py` — prefix `→` `[zf]`, compact state suffix format
- `hooks/session-resume.py` — collapse 5+ lines to 2-3, shorten labels, compress workflow line
- `commands/status.md` — trim table padding, inline pipeline row, shorten section headers
- `commands/next.md` — minor label compression if any

**Out:**
- Changing structured machine-parseable formats (ROADMAP section markers, frontmatter)
- Removing decision-relevant content (test status, drift count, stage)
- Altering dedup/cache logic

## Files Changed

- `hooks/intent-sdlc.py`
- `hooks/session-resume.py`
- `commands/status.md`
- `commands/next.md`