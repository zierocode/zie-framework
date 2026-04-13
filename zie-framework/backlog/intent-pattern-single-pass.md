---
tags: [chore]
---

# Intent Pattern Single-Pass Regex — 65 checks → 1

## Problem

13 intent categories × ~5 patterns = ~65 regex checks per message; short-msg gate exits early but still scans all. Patterns checked sequentially; no early-exit on first match.

## Motivation

Single combined regex with named groups; one-pass match → intent extraction. Cache last 10 messages for dedup.

## Rough Scope

**In:**
- `hooks/intent-sdlc.py` lines 85-140 — refactor to single regex
- Named groups for intent extraction
- Message cache (last 10)

**Out:**
- Intent categories (unchanged)

<!-- priority: HIGH -->
<!-- depends_on: none -->
