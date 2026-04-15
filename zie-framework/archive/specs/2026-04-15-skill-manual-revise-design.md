---
date: 2026-04-15
status: approved
slug: skill-manual-revise
backlog: backlog/skill-manual-revise.md
---

# skill-manual-revise — Compress SKILL.md Files

## Problem

All 14 `SKILL.md` files (1492 total lines) contain verbose prose that adds token cost on every skill invocation. Files like `spec-design` (173 lines) and `write-plan` (142 lines) can be compressed 20-30% without losing functionality by using tables, removing redundancy, and tightening phrasing.

## Solution

Manually revise each SKILL.md file to reduce word count while preserving all instructions, arguments, steps, and behavioural rules. Apply these compression tactics consistently:

- **Tables for structured data** — convert prose argument descriptions and size guides to compact tables (already used in some files; standardise)
- **Eliminate redundant explanation** — remove sentences that restate what the next step already shows; keep one authoritative statement
- **Tighten phrasing** — shorter imperatives ("Run tests" not "You should run the tests to verify"), drop filler words
- **Collapse memory blocks** — replace verbose `zie_memory_enabled` call descriptions with a one-line template: `→ zie-memory: recall(…)` / `→ zie-memory: remember(…)`
- **Keep Thai headers** — bilingual headers stay; compress the English body text under them

## Rough Scope

**In:**
- Revise all 14 `SKILL.md` files in `skills/`
- Target: 20% total line reduction (1492 → ~1190 lines)
- Verify each skill still works after compression (functional parity)
- Preserve frontmatter, argument specs, TDD steps, and all behavioural rules

**Out:**
- Changing skill behaviour or workflow steps
- Removing essential instructions that affect correctness
- Altering file names or directory structure

## Files Changed

| File | Current Lines | Target |
| --- | --- | --- |
| `skills/spec-design/SKILL.md` | 173 | ~140 |
| `skills/write-plan/SKILL.md` | 142 | ~115 |
| `skills/brainstorm/SKILL.md` | 141 | ~115 |
| `skills/zie-audit/SKILL.md` | 137 | ~110 |
| `skills/plan-reviewer/SKILL.md` | 137 | ~110 |
| `skills/verify/SKILL.md` | 133 | ~107 |
| `skills/impl-reviewer/SKILL.md` | 111 | ~90 |
| `skills/spec-reviewer/SKILL.md` | 106 | ~85 |
| `skills/docs-sync-check/SKILL.md` | 100 | ~80 |
| `skills/test-pyramid/SKILL.md` | 83 | ~68 |
| `skills/debug/SKILL.md` | 69 | ~56 |
| `skills/tdd-loop/SKILL.md` | 61 | ~50 |
| `skills/load-context/SKILL.md` | 57 | ~46 |
| `skills/using-zie-framework/SKILL.md` | 42 | ~35 |