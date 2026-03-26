---
description: Project audit — Security, Code Health, and Structural dimensions. Produces scored findings for backlog.
allowed-tools: Read, Bash, Glob, Grep, Skill, Agent, WebSearch, WebFetch
model: sonnet
effort: medium
---

# /zie-audit — Project Audit

Audit the codebase across Security, Code Health, and Structural dimensions.
Produces scored findings for backlog prioritization.

## Phase 1 — Research Profile

Read manifests (`package.json` / `pyproject.toml` / `go.mod` / etc.) to build:
- `stack`: languages + frameworks detected
- `domain`: app type (web API / CLI / plugin / data pipeline)
- `deps`: key dependencies + versions

## Phase 2 — Parallel Dimension Scan

Spawn 3 Agents **simultaneously** (max 4 parallel):

**Agent 1 — Security**
Focus: hardcoded secrets, shell injection, input validation, auth gaps,
error leakage, path traversal. Max 5 WebSearch queries (CVEs, known patterns).
Output: findings list with severity (CRITICAL / HIGH / MEDIUM / LOW).

**Agent 2 — Code Health** (Lean + Quality + Testing)
Focus: dead code, duplication, over-engineering, untested modules, weak
assertions, coverage gaps, fragile tests. Max 5 WebSearch queries.
Output: findings list with severity.

**Agent 3 — Structural** (Docs + Architecture)
Focus: stale docs, broken examples, coupling violations, SRP issues,
inconsistent naming, silent failures, missing interfaces. Max 5 WebSearch.
Output: findings list with severity.

Wait for all 3 agents before Phase 3.

## Phase 3 — Synthesis

Spawn 1 Agent with all 3 dimension outputs (no WebSearch):
- Deduplicate overlapping findings across dimensions
- Score each finding (1–10 impact × 1–10 effort)
- Rank: CRITICAL first, then by score descending
- Flag coverage gaps (dimensions with fewer than 3 findings)
- Produce final scored report

## Phase 4 — Backlog Integration

For each CRITICAL or HIGH finding:
- Ask Zie: "Add to backlog? (yes / skip)"
- If yes: create `zie-framework/backlog/<slug>.md` + update ROADMAP Next

## Output Format

Print scored report with dimension headers, finding descriptions, severity,
and recommended action. Save to `zie-framework/audit-<date>.md` if Zie confirms.
