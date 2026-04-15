---
tags: [chore]
---

# Compress Retro Command

## Problem

`/retro` is 1,181 words with verbose sections:
- Self-tuning proposals (18 lines of git log pattern checking) — speculative, rarely effective
- Subagent activity parsing (3 lines for a feature that may not exist)
- Done-rotation logic (7 lines for straightforward date math)

Estimated reduction: ~500 words → ~680 words remaining.

## Motivation

Retro fires at session end when context is often near capacity. Every token saved here is especially valuable.

## Rough Scope

**In:**
- Compress self-tuning to 2-line summary ("scan git_log_raw for RED-cycle patterns and stale safety_check_mode, print advisory proposals")
- Compress subagent activity to 1 line
- Compress done-rotation to 2-line rule

**Out:**
- Removing self-tuning feature entirely (compress, don't remove)