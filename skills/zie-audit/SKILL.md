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
| 0 | `$ARGUMENTS[0]` | Optional `--focus <dimension>` flag | absent → full 9-dimension audit |

When `--focus <dimension>` is provided: Phase 2 runs only the matching agent;
Phase 3 researches only that dimension (deeply). All other phases run normally.

Focus map (for agent selection):
- `security`, `deps` → Agent A
- `code`, `perf` → Agent B
- `structure`, `obs` → Agent E
- `external` → Phase 3 only

If unrecognized focus value → print warning and run full audit (all agents).
`active_agents` controls conditional agent spawn: only agents in `active_agents` are spawned.

## Pre-flight

1. Check `zie-framework/` exists — if not, tell user to run `/init` first.
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

Read `zie-framework/ROADMAP.md` → extract existing backlog slugs from Next + Ready lanes.
Read `zie-framework/decisions/` → list ADR filenames (skip flagging intentional decisions).
Run `git log --oneline -15` → bind as `git_log` (higher weight for recently-changed code).

`shared_context = { research_profile, backlog_slugs, adr_filenames, git_log }`

## Phase 2 — Parallel Internal Analysis

Spawn 5 parallel agents via `Agent` tool. Each receives `research_profile`.

- **Agent A — Security + Dependency Health**: secrets, shell injection, input
  validation, auth, error leakage, outdated deps with CVE hints; overly-loose
  version pins, license risks, deps with actively-maintained alternatives
- **Agent B — Lean / Efficiency**: dead code, duplicated logic, over-engineering,
  unnecessary dependencies; async/hot-path perf checks, N+1 patterns, missing
  caching for repeated expensive calls, blocking calls in hot paths
- **Agent C — Quality / Testing**: untested modules, fragile tests, weak
  assertions, missing edge cases, TODO/FIXME count
- **Agent D — Docs**: stale references, missing docs, broken examples,
  README completeness, CHANGELOG/VERSION sync
- **Agent E — Architecture + Observability**: high coupling, SRP violations,
  inconsistent patterns, silent failures; missing health check endpoints,
  unstructured error reporting, missing metrics hooks, no graceful shutdown;
  MCP Server Usage check: read `~/.claude/settings.json` (global) and
  `.claude/settings.json` (repo-local) to build `configured_servers`.
  If neither exists or `mcpServers` is absent → skip this check entirely.
  Grep `commands/*.md` and `skills/*/SKILL.md` for `mcp__<name>__`.
  Zero matches → emit LOW finding: server configured but never referenced —
  consider removing to reduce context overhead

Sub-checks distributed across agents: Performance (B/E), Dependency Health (A/C),
Developer Experience (D), Standards compliance (E).

Each agent receives `research_profile`. Do not re-read project manifests, git log, or ADR lists — they are in shared_context.

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

Filter: remove any finding whose slug matches an existing backlog slug or ADR
filename (already tracked or intentionally decided — skip).

Categorize:
- **Quick Win** — Impact ≥ 3 and Effort ≤ 2
- **Strategic** — Impact ≥ 4 and Effort > 2
- **Defer** — Impact < 3

no WebSearch in this phase — synthesis only.

## Phase 5 — Report + Backlog Selection

Print scored report (Overall Score, 9 dimension scores, findings by severity:
CRITICAL / HIGH / MEDIUM / LOW).
Save to `zie-framework/evidence/audit-YYYY-MM-DD.md` (gitignored).

Show all CRITICAL + HIGH findings at once and ask once per group:
```
CRITICAL findings (N): ...  Add all CRITICAL to backlog? (yes / no)
HIGH findings (N): ...      Add to backlog: (all / select numbers / skip)
```

For each selected finding: create `zie-framework/backlog/<slug>.md` and add to
`zie-framework/ROADMAP.md` Next lane.

## Notes

- Always deep — no quick mode; external research always runs
- Typical runtime: 3–8 minutes (parallel agents + web research)
- Evidence saved to `zie-framework/evidence/` — never committed
