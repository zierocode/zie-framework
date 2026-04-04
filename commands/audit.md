---
description: Project audit — Security, Code Health, Performance, Structural, Dependency Health, Observability, and External Research dimensions. Produces scored findings for backlog.
allowed-tools: Read, Bash, Glob, Grep, Skill, Agent, WebSearch, WebFetch
model: sonnet
effort: medium
---

# /audit — Project Audit

Audit the codebase across 7 dimensions plus external research.
Produces scored findings filtered against existing backlog.

## Arguments

| Flag | Values | Description |
| --- | --- | --- |
| `--focus` | `security`, `deps`, `code`, `perf`, `structure`, `obs`, `external` | Limit audit to specific dimensions. Comma-separated for multiple (e.g. `--focus security,code`). Omit to run all 4 agents. |

**Focus map:** `security` → Agent 1 | `deps` → Agent 1 | `code` → Agent 2 | `perf` → Agent 2 | `structure` → Agent 3 | `obs` → Agent 3 | `external` → Agent 4

**Parse at command start:**
```python
focus_tokens = []
for arg in ARGUMENTS.split():
    if arg.startswith("--focus"):
        val = arg.split("=")[-1] if "=" in arg else ""
        focus_tokens = [t.strip() for t in val.split(",") if t.strip()]
        break

focus_map = {
    "security": [1], "deps": [1],
    "code": [2], "perf": [2],
    "structure": [3], "obs": [3],
    "external": [4],
}
active_agents = set()
for token in focus_tokens:
    if token in focus_map:
        active_agents.update(focus_map[token])
    else:
        print(f"⚠ Unknown focus value '{token}' — running full audit")
        active_agents = {1, 2, 3, 4}
        break
if not active_agents:
    active_agents = {1, 2, 3, 4}  # default: all agents
```

## Phase 1 — Context Bundle

Print: `[Phase 1/4] Context Bundle`

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
- `zie-framework/decisions/` → list ADR filenames + read content (intentional decisions — skip flagging these)

**Recent activity** — run `git log --oneline -15` → `git_log` (audit gives higher weight to new code)

**ADR cache** — call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
- Returns `(True, adr_cache_path)` → save path
- Returns `(False, None)` → set `adr_cache_path = None`

**Bundle:** `shared_context = { stack, domain, deps, backlog_slugs, adrs_filenames, git_log, adr_cache_path }`

## Phase 2 — Parallel Dimension Scan

Print: `[Phase 2/4] Parallel Dimension Scan`

Print header: `## Phase 2 — Parallel Dimension Scan (active: Agent N, ...)`. Each agent is conditional: only spawn if agent number in `active_agents`.
After each agent completes, print: `Agent {X} ({Domain}) ✓` (e.g. `Agent 1 (Security/Deps) ✓`).
Before each WebSearch call, print: `[Research {N}/15]` (increment N per call, cap at 15).

Spawn up to 4 Agents **simultaneously** (`run_in_background: true`). Pass `shared_context`
to each with instruction: **"Do not re-read project manifests, git log, or ADR lists — they are in shared_context."**

**Agent 1 — Security + Dependency Health**

Receives `shared_context` — use `deps` and `stack` directly; do not re-read manifests.

Security focus: hardcoded secrets, shell injection, input validation gaps, auth
holes, error message leakage, path traversal, unsafe deserialization.

Dependency Health focus: outdated deps with known issues, unused deps,
overly-loose version pins, license risks, deps with actively maintained
alternatives.

WebSearch: max 6 queries — CVEs for specific `{shared_context.deps}` versions, dependency
advisories. No generic searches; queries must reference actual dep names+versions
from shared_context.

Output: findings list with severity (CRITICAL / HIGH / MEDIUM / LOW).

**Agent 2 — Code Health + Performance**

Receives `shared_context` — use `stack` and `git_log` directly; do not re-read git history.

Code Health focus: dead code, duplication above threshold, over-engineering,
untested modules, weak assertions, coverage gaps, fragile tests, error paths
silently swallowed.

Performance focus: sync operations in async context, N+1 query patterns,
missing caching for repeated expensive calls, blocking calls in hot paths,
connection pool exhaustion risks, unbounded memory growth patterns.

WebSearch: max 2 queries — only if a specific dep/framework has known
performance footguns relevant to `{shared_context.stack}`.

**MCP Server Usage check** (context efficiency):

Read settings files to build the configured server list:
1. Expand `~/.claude/settings.json` to absolute path. Read if it exists.
2. Read `.claude/settings.json` (repo-root-relative) if it exists.
3. From each file that exists, extract keys of the `mcpServers` object. Union all keys across both files into `configured_servers`.
4. If no settings file exists, or `mcpServers` is absent or `{}` in all found files → skip this check entirely (no output).

For each name in `configured_servers`:
- Grep `commands/*.md` and `skills/*/SKILL.md` for the literal prefix `mcp__<name>__`.
- If zero matches found across both scopes → emit LOW finding: `MCP server '<name>' configured but never referenced in commands or skills — consider removing to reduce context overhead`
- If at least one match found → no finding for this server (clean pass).

Output: findings list with severity.

**Agent 3 — Structural + Observability**

Receives `shared_context` — use `adrs_filenames` to avoid flagging intentional decisions.

Structural focus: stale/wrong docs, broken examples, coupling violations,
SRP issues, inconsistent naming conventions, missing abstractions causing
repetition, circular dependencies.

Observability focus: missing health check endpoints, unstructured error
reporting (no log levels / no error IDs), missing metrics hooks, no graceful
shutdown handling, silent crash paths.

WebSearch: max 2 queries — only for `{shared_context.domain}`-specific structural conventions
(e.g., "REST API versioning patterns" if domain is web API).

Output: findings list with severity.

**Agent 4 — External Research** ← improvement-focused, not bug-finding

Receives `shared_context` — use `stack` and `domain` directly.

Goal: discover what projects using `{shared_context.stack}` for `{shared_context.domain}` *should have* that
this project is likely missing. Frame every finding as an actionable improvement,
not a defect.

Research vectors (use detected `{shared_context.stack}` and `{shared_context.domain}` as search terms — do
NOT hardcode language names):
- Best practices: `"{stack} {domain} production best practices"`
- Ecosystem norms: `"{stack} project structure conventions"`
- Tooling gaps: `"{domain} developer tooling 2024"` (CI, linting, type safety)
- Resilience patterns: `"{domain} resilience patterns {stack}"`
- Community standards: what does the `{stack}` community consider table stakes?

WebSearch: max 6 queries — all must reference detected `{shared_context.stack}` or `{shared_context.domain}`.
WebFetch: follow top 2 authoritative results (official docs, well-known guides).

Output: improvement opportunities list with rationale and source URLs. Format:
"Projects using {stack} for {domain} typically have X. This project appears to
be missing Y because Z."

---

Wait for all 4 agents before Phase 3.

## Phase 3 — Synthesis

Print: `[Phase 3/4] Synthesis`

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

Print: `[Phase 4/4] Findings Output`

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
