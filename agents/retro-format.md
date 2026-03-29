---
description: Format a retrospective summary from a compact JSON bundle. Produces five structured retro sections and ADR entries.
background: true
allowed-tools: Read, Glob, Grep
---

# retro-format agent

Invoke `Skill(zie-framework:retro-format)` with the compact JSON bundle passed
in `$ARGUMENTS` by `/zie-retro`.

Produce all five retro sections (What Shipped, What Worked, What Didn't Work,
Key Decisions, Learnings). Return the formatted output to the caller.
