---
name: zie-audit
description: Deep project audit — 9-dimension analysis with external research. Produces scored findings for backlog.
argument-hint: "[--focus <dimension>]"
metadata:
  zie_memory_enabled: false
model: opus
effort: high
---

# zie-audit — Deep Project Audit

Systematic 9-dimension analysis: internal codebase scan + external research.
Produces a scored report and feeds selected findings into the backlog.

Invoked by: `Skill(zie-framework:zie-audit)` from `/zie-audit`.

## Arguments

| Position | Variable | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | Optional `--focus <dimension>` flag | absent → full 9-dimension audit |

When `--focus <dimension>` is provided: Phase 2 runs only the matching agent;
Phase 3 researches only that dimension (deeply). All other phases run normally.

## Pre-flight

1. Check `zie-framework/` exists — if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → project name, project_type, test_runner, has_frontend.
3. Read `zie-framework/PROJECT.md` → tech stack, description.

## Load Reference Material

Read `${CLAUDE_SKILL_DIR}/reference.md` for:

- Dimension definitions and what each agent checks
- Scoring rubric (start-at-100, per-severity deductions)
- Query template library for Phase 3

If `${CLAUDE_SKILL_DIR}/reference.md` is not found, skip gracefully — use
built-in knowledge for dimension definitions and scoring. Note the gap in the
audit report header. Never block the audit.

## Phase 1 — Project Intelligence

Build `research_profile` (languages, frameworks, domain, deps, project_type,
test_runner, has_frontend, deployment, special_ctx). Detect from:
`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`,
`Dockerfile`, `docker-compose.yml`, `.config`, source files.

## Phase 2 — Parallel Internal Analysis

Spawn 5 parallel agents via `Agent` tool. Each receives `research_profile`.

- **Agent A — Security**: secrets, shell injection, input validation, auth,
  error leakage, outdated deps with CVE hints
- **Agent B — Lean / Efficiency**: dead code, duplicated logic, over-engineering,
  unnecessary dependencies
- **Agent C — Quality / Testing**: untested modules, fragile tests, weak
  assertions, missing edge cases, TODO/FIXME count
- **Agent D — Docs**: stale references, missing docs, broken examples,
  README completeness, CHANGELOG/VERSION sync
- **Agent E — Architecture**: high coupling, SRP violations, inconsistent
  patterns, silent failures

Sub-checks distributed across agents: Performance (B/E), Dependency Health (A/C),
Developer Experience (D), Standards compliance (E).

Each agent returns: `[{severity, dimension, description, location, effort}]`

## Phase 3 — Dynamic External Research

Build query list from `research_profile` using the query template library in
`reference.md`. Cap at 15 queries. Run `WebSearch` per query; use `WebFetch`
for high-value results. Skip failed queries gracefully — note in report.

Synthesize into `external_standards_report`:
each dimension → `[{standard, finding, severity}]`

## Phase 4 — Synthesis

Cross-reference Phase 2 + Phase 3. Bump severity one level for findings present
in both (external validation = higher confidence). Deduplicate. Score each
dimension using the rubric in `reference.md`. Compute weighted overall score.

## Phase 5 — Report + Backlog Selection

Print scored report (Overall Score, 9 dimension scores, findings by severity).
Save to `zie-framework/evidence/audit-YYYY-MM-DD.md` (gitignored).

Prompt: `Add to backlog: enter numbers, "high", "all", or "none"`

For each selected finding: create `zie-framework/backlog/<slug>.md` and add to
`zie-framework/ROADMAP.md` Next lane.

## Notes

- Always deep — no quick mode; external research always runs
- Typical runtime: 3–8 minutes (parallel agents + web research)
- Evidence saved to `zie-framework/evidence/` — never committed
