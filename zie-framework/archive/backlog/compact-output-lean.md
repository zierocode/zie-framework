---
tags: [performance]
---

# Compact Hook and Command Output

## Problem

Hook output and command output contains verbose logging and formatting that adds token cost. `/status` output, `/next` output, and hook messages can be compressed by 15-25%.

## Rough Scope

**In:**
- Compress output from `intent-sdlc`, `session-resume`, and `status`/`next` commands
- Remove verbose labels, use shorter format strings
- Strip unnecessary newlines and padding
- Target 15-25% token reduction in typical output

**Out:**
- Removing information that's needed for decision-making
- Changing the structured format (keep machine-parseable sections intact)

## Priority

MEDIUM