---
name: zie-audit
description: Deep project audit — 9-dimension analysis with external research. Produces scored findings for backlog.
argument-hint: "[--focus <dimension>]"
metadata:
  zie_memory_enabled: false
model: sonnet
effort: medium
---

# zie-audit — Deep Project Audit

Systematic 9-dimension analysis: internal codebase scan + external research.
Produces a scored report and feeds selected findings into the backlog.

Invoked by: `Skill(zie-framework:zie-audit)` from `/audit`.

## Arguments

| Position | Variable | Description | Default |
| --- | --- | --- | --- |
| 0 | `$ARGUMENTS[0]` | `--focus <dimension>` flag | absent → full 9-dimension audit |

Focus map (controls which agent runs in Phase 2):
- `security`, `deps` → Agent A
- `code`, `perf` → Agent B
- `structure`, `obs` → Agent E
- `external` → Phase 3 only

Unrecognized focus → warning + full audit (all agents). `active_agents` controls conditional spawn.

## Pre-flight

1. Check `zie-framework/` exists — missing → tell user to run `/init`.
2. Read `zie-framework/.config` → project name, project_type, test_runner, has_frontend.
3. Read `zie-framework/PROJECT.md` → tech stack, description.

## Load Reference Material

Read `${CLAUDE_SKILL_DIR}/reference.md` for dimension definitions, scoring rubric, Phase 3 query templates.
If not found → skip gracefully, use built-in knowledge. Note gap in report header. Never block the audit.

## Phase 1 — Project Intelligence

Build `research_profile` from: `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `Dockerfile`, `docker-compose.yml`, `.config`, source files → languages, frameworks, domain, deps, project_type, test_runner, has_frontend, deployment, special_ctx.

Read `zie-framework/ROADMAP.md` → extract backlog slugs from Next + Ready lanes.
Read `zie-framework/decisions/` → list ADR filenames.
Run `git log --oneline -15` → bind as `git_log` (higher weight for recently-changed code).

`shared_context = { research_profile, backlog_slugs, adr_filenames, git_log }`

## Phase 2 — Parallel Internal Analysis

Spawn 5 parallel agents via `Agent` tool. Each receives `research_profile`. Do not re-read project manifests, git log, or ADR lists — they are in shared_context.

| Agent | Scope |
| --- | --- |
| **A** | Security + Dependency Health: secrets, shell injection, input validation, auth, error leakage, outdated deps/CVE hints, loose version pins, license risks, better alternatives |
| **B** | Lean / Efficiency: dead code, duplication, over-engineering, unnecessary deps; async/hot-path perf, N+1 patterns, missing cache for expensive calls, blocking in hot paths |
| **C** | Quality / Testing: untested modules, fragile tests, weak assertions, missing edge cases, TODO/FIXME count |
| **D** | Docs: stale references, missing docs, broken examples, README completeness, CHANGELOG/VERSION sync |
| **E** | Architecture + Observability: high coupling, SRP violations, inconsistent patterns, silent failures; missing health endpoints, unstructured errors, missing metrics, no graceful shutdown; MCP Server Usage: read `~/.claude/settings.json` (global) + `.claude/settings.json` (local) → `configured_servers`. No `mcpServers` → skip. Grep `commands/*.md` and `skills/*/SKILL.md` for `mcp__<name>__`. Zero matches → LOW finding: server configured but never referenced |

Each agent returns: `[{severity, dimension, description, location, effort}]`

## Phase 3 — Dynamic External Research

Build query list from `research_profile` using template library in `reference.md`. Cap at 15 queries. Run `WebSearch` per query; `WebFetch` for high-value results. Skip failed queries — note in report.

Synthesize into `external_standards_report`: each dimension → `[{standard, finding, severity}]`

## Phase 4 — Synthesis

Cross-reference Phase 2 + Phase 3. Bump severity one level for findings in both (external validation = higher confidence). Deduplicate. Score each dimension using rubric in `reference.md`. Compute weighted overall score.

Filter: remove findings whose slug matches an existing backlog slug or ADR filename (already tracked or intentionally decided).

Categorize: **Quick Win** (Impact ≥ 3, Effort ≤ 2) · **Strategic** (Impact ≥ 4, Effort > 2) · **Defer** (Impact < 3).

No WebSearch in this phase — synthesis only.

## Phase 5 — Report + Backlog Selection

Print scored report (Overall Score, 9 dimension scores, findings by severity: CRITICAL / HIGH / MEDIUM / LOW).
Save to `zie-framework/evidence/audit-YYYY-MM-DD.md` (gitignored).

Show all CRITICAL + HIGH findings, ask once per group:
```
CRITICAL findings (N): ...  Add all CRITICAL to backlog? (yes / no)
HIGH findings (N): ...      Add to backlog: (all / select numbers / skip)
```

For each selected finding: create `zie-framework/backlog/<slug>.md` and add to `zie-framework/ROADMAP.md` Next lane.