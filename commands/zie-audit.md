---
description: Project audit — Security, Code Health, Performance, Structural, Dependency Health, Observability, and External Research dimensions. Produces scored findings for backlog.
allowed-tools: Read, Bash, Glob, Grep, Skill, Agent, WebSearch, WebFetch
model: sonnet
effort: medium
---

# /zie-audit — Project Audit

Audit the codebase across 7 dimensions plus external research.
Produces scored findings filtered against existing backlog.

## Phase 1 — Context Bundle

Build a context bundle for all downstream agents. All reads are inline — no
agent needed.

**Manifests** — read whichever exist (generic, not language-specific):
`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `build.gradle`,
`mix.exs`, `composer.json`, `Gemfile`

Extract:
- `stack` — languages + frameworks detected
- `domain` — app type (web API / CLI / plugin / data pipeline / library / other)
- `deps` — key dependencies with versions

**SDLC context** — read to avoid redundant findings:
- `zie-framework/ROADMAP.md` → extract backlog slugs from Next + Ready lanes
- `zie-framework/decisions/` → list ADR filenames (intentional decisions — skip flagging these)

**Recent activity** — run `git log --oneline -15` → note recently changed files
(audit gives higher weight to new code)

## Phase 2 — Parallel Dimension Scan

Spawn 4 Agents **simultaneously** (`run_in_background: true`). Pass `stack`,
`domain`, `deps` to each.

**Agent 1 — Security + Dependency Health**

Security focus: hardcoded secrets, shell injection, input validation gaps, auth
holes, error message leakage, path traversal, unsafe deserialization.

Dependency Health focus: outdated deps with known issues, unused deps,
overly-loose version pins, license risks, deps with actively maintained
alternatives.

WebSearch: max 6 queries — CVEs for specific `{deps}` versions, dependency
advisories. No generic searches; queries must reference actual dep names+versions
from Phase 1.

Output: findings list with severity (CRITICAL / HIGH / MEDIUM / LOW).

**Agent 2 — Code Health + Performance**

Code Health focus: dead code, duplication above threshold, over-engineering,
untested modules, weak assertions, coverage gaps, fragile tests, error paths
silently swallowed.

Performance focus: sync operations in async context, N+1 query patterns,
missing caching for repeated expensive calls, blocking calls in hot paths,
connection pool exhaustion risks, unbounded memory growth patterns.

WebSearch: max 2 queries — only if a specific dep/framework has known
performance footguns relevant to `{stack}`.

Output: findings list with severity.

**Agent 3 — Structural + Observability**

Structural focus: stale/wrong docs, broken examples, coupling violations,
SRP issues, inconsistent naming conventions, missing abstractions causing
repetition, circular dependencies.

Observability focus: missing health check endpoints, unstructured error
reporting (no log levels / no error IDs), missing metrics hooks, no graceful
shutdown handling, silent crash paths.

WebSearch: max 2 queries — only for `{domain}`-specific structural conventions
(e.g., "REST API versioning patterns" if domain is web API).

Output: findings list with severity.

**Agent 4 — External Research** ← improvement-focused, not bug-finding

Goal: discover what projects using `{stack}` for `{domain}` *should have* that
this project is likely missing. Frame every finding as an actionable improvement,
not a defect.

Research vectors (use detected `{stack}` and `{domain}` as search terms — do
NOT hardcode language names):
- Best practices: `"{stack} {domain} production best practices"`
- Ecosystem norms: `"{stack} project structure conventions"`
- Tooling gaps: `"{domain} developer tooling 2024"` (CI, linting, type safety)
- Resilience patterns: `"{domain} resilience patterns {stack}"`
- Community standards: what does the `{stack}` community consider table stakes?

WebSearch: max 6 queries — all must reference detected `{stack}` or `{domain}`.
WebFetch: follow top 2 authoritative results (official docs, well-known guides).

Output: improvement opportunities list with rationale and source URLs. Format:
"Projects using {stack} for {domain} typically have X. This project appears to
be missing Y because Z."

---

Wait for all 4 agents before Phase 3.

## Phase 3 — Synthesis

no WebSearch — inline synthesis, no additional agent needed.

1. **Filter** — remove any finding whose slug matches an existing backlog item
   or ADR (collected in Phase 1). These are already tracked or intentionally
   decided.

2. **Deduplicate** — merge overlapping findings across agents. Keep the highest
   severity when same issue appears in multiple agents.

3. **Score** — for each finding assign:
   - Impact: 1–5 (5 = project-threatening)
   - Effort: 1–5 (1 = under 30 min, 5 = week+)

4. **Categorize**:
   - **Quick Win** — Impact ≥ 3 and Effort ≤ 2
   - **Strategic** — Impact ≥ 4 and Effort > 2
   - **Defer** — Impact < 3 (log but don't push to backlog)

5. **Rank** — CRITICAL first, then Quick Wins, then Strategic, then Defer.
   Within each group: by Impact descending.

6. Print scored report:

```
## Audit Report — <date>

### CRITICAL
| Finding | Dimension | Impact | Effort | Category |
...

### HIGH — Quick Wins
...

### HIGH — Strategic
...

### MEDIUM / LOW — Deferred
...

Dimensions with 0 findings: <list or "none">
```

## Phase 4 — Batch Backlog Integration

Show all CRITICAL + HIGH findings at once. Ask once per group:

```
CRITICAL findings (N):
  1. <slug> — <title>
  2. ...
Add all CRITICAL to backlog? (yes / no)

HIGH findings (N):
  1. <slug> — <title>  [Quick Win]
  2. ...
Add to backlog: (all / select numbers e.g. 1,3 / skip)
```

For each selected finding:
- Create `zie-framework/backlog/<slug>.md`
- Add to ROADMAP Next lane under appropriate priority

If Zie confirms: save full report to `zie-framework/audit-<YYYY-MM-DD>.md`.
