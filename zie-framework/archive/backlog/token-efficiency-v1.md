---
tags: [chore]
---

# Token Efficiency v1 — ADR Summary Gate + Cache Structure + Prompt Compression

## Problem

zie-framework spends tokens unnecessarily in three areas:
1. **Reviewers load all ADRs every pass** — 55+ ADR files (~3,000–8,000 tokens) loaded by spec-reviewer, plan-reviewer, and impl-reviewer on every pipeline run, even when no conflict exists
2. **CLAUDE.md cache-unfriendly structure** — dynamic content (version numbers) sits near the top, busting CC's system-prompt cache prefix on every release
3. **Skill/command prompts contain residual verbosity** — redundant phase headers, fallback restatements, and tutorial prose that v1.19.0 didn't fully trim

## Motivation

Every pipeline run (spec→plan→implement) invokes 3+ reviewer passes. Fixing area 1 alone saves thousands of tokens per run. Areas 2 and 3 compound across every session and every subagent spawn. This is the highest-ROI efficiency work remaining after the v1.19.0 lean sprint.

## Rough Scope

**A — ADR Summary Gate**
- `reviewer-context` + `load-context` skills: load only `ADR-000-summary.md` (≤300 tokens) by default
- Load full ADR file only when summary flags a specific conflict
- `/retro`: auto-update `ADR-000-summary.md` via haiku pass after each release
- `ADR-000-summary.md`: reformat as 1-line-per-ADR index (~5 tokens each)

**B — CLAUDE.md Prompt Cache Structure**
- Reorder CLAUDE.md: stable content (Project Structure, Key Rules, Hook Ref Docs) → top
- Dynamic content (Tech Stack with version refs, optional dep notes) → bottom
- Add `<!-- STABLE -->` / `<!-- DYNAMIC -->` marker comments

**C — Skill/Command Prompt Compression**
- Audit all 12 skills + 14 commands with `wc -w` baseline
- Remove: redundant phase headers, fallback restatements, "Notes" sections that restate rules, verbose output format blocks
- Keep: checklists, required steps, format specs, logic enforced by tests
- Target: 20–30% word count reduction per file
- Gate: `make test-unit` must pass (tests enforce command content)

**Out of scope:** changing what any skill/command does; removing acceptance criteria or checklist items

**Supersedes:** `backlog/token-efficiency-sprint.md`, `backlog/skill-content-pruning.md`
