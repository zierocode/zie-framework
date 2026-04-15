---
tags: [chore]
---

# Lean Compact Output

## Problem

`sdlc-compact.py` lists up to 20 changed files as individual `- filename` lines during PostCompact context injection. Compact events occur when context is near capacity, making every token count. Listing 20 filenames wastes ~100-200 tokens at the worst possible time.

## Motivation

Compact context is the most token-expensive context in the entire session. A summary line ("20 files changed") would suffice and save ~100-200 tokens per compact event.

## Rough Scope

**In:**
- Replace individual file listing with summary: "N files changed in paths: dir1/, dir2/, dir3/" (max 3 directory names)
- Keep file listing only when N <= 5

**Out:**
- Changing compact recovery logic
- Changing what data sdlc-compact collects