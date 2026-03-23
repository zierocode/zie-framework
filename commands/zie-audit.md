---
description: Deep project audit — 9-dimension analysis with dynamic external
  research. Produces a scored findings report for backlog selection.
allowed-tools: Read, Bash, Glob, Grep, Skill, Agent, WebSearch, WebFetch
---

# /zie-audit — Deep Project Audit

Systematic 9-dimension analysis combining internal codebase scan with dynamic
external research. Produces a scored report and feeds selected findings into the
backlog.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → project name, project_type, test_runner,
   has_frontend.
3. Read `zie-framework/PROJECT.md` → tech stack, description.

## Phase 1 — Project Intelligence

Build `research_profile` to drive all downstream phases:

```text
research_profile = {
  languages:    [],   # e.g. ["python", "typescript"]
  frameworks:   [],   # e.g. ["pytest", "next.js", "fastapi"]
  domain:       "",   # e.g. "claude-code-plugin", "web-api", "cli-tool"
  deps:         {},   # name → version, top 20 by import frequency
  project_type: "",   # from .config
  test_runner:  "",   # from .config
  has_frontend: bool,
  deployment:   "",   # "vercel" | "docker" | "pip-package" | "unknown"
  special_ctx:  []    # ["handles-payments","processes-pii","public-api",...]
}
```

Detect from: `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`,
`Cargo.toml`, `Dockerfile`, `docker-compose.yml`, `.config`, source files.

If `--focus <dimension>` provided → note it; Phase 2 skips other dimensions;
Phase 3 researches only that dimension (but deeply).

## Phase 2 — Parallel Internal Analysis

Spawn 5 parallel agents via `Agent` tool. Each receives `research_profile` and
full codebase access. Each returns a findings list:
`[{severity, dimension, description, location, effort}]`

### Agent A — Security

Stack-aware checks using `research_profile.languages` and
`research_profile.frameworks`:

- Hardcoded secrets or credentials in any file
- Shell injection: `subprocess`, `os.system`, `eval`, `exec` without
  input sanitization
- Input validation gaps: external inputs used without sanitization
- Auth/authz patterns: are protected routes actually protected?
- Error messages leaking internals (stack traces, paths, keys)
- Dependency versions with known CVE hints (flag outdated major versions)

### Agent B — Lean / Efficiency

- Dead code: functions, classes, or imports never referenced
- Duplicated logic: same algorithm present in 2+ places
- Over-engineering: abstractions with only one concrete use case
- Repeated boilerplate that could be extracted
- Unnecessary dependencies (imported but barely used)

### Agent C — Quality / Testing

- Untested modules: public functions with no test coverage
- Fragile tests: `time.sleep()`, order-dependent, shared mutable state
- Weak assertions: tests that pass even if behavior is wrong
- Missing edge cases: empty input, None, boundary values, error paths
- TODO/FIXME/PLACEHOLDER count with file + line locations

### Agent D — Documentation

- Stale references: docs mention removed commands, APIs, or versions
- Missing docs: public interfaces without any documentation
- Broken examples: code blocks that won't work as written
- README completeness: setup steps, usage, troubleshooting present?
- CHANGELOG + VERSION in sync

### Agent E — Architecture

- High coupling: components with too many cross-module dependencies
- SRP violations: modules clearly doing more than one thing
- Inconsistent patterns: same problem solved differently in 2+ places
- Silent failures: exceptions caught and swallowed without logging

Sub-checks distributed across agents by relevance:

- **Performance**: hot paths, I/O patterns, caching opportunities (Agent B/E)
- **Dependency Health**: outdated packages, license compatibility (Agent A/C)
- **Developer Experience**: output clarity, error messages, onboarding (Agent D)
- **Standards compliance**: semver, conventional commits, OpenSSF, SLSA (Agent E)

## Phase 3 — Dynamic External Research

Research agent builds queries from `research_profile` — never hardcoded:

```text
queries = []

# Language / runtime standards
for lang in research_profile.languages:
    queries += ["{lang} best practices 2026",
                "{lang} security vulnerabilities checklist"]

# Framework-specific guides
for fw in research_profile.frameworks:
    queries += ["{fw} security guide",
                "{fw} performance anti-patterns"]

# Domain-specific standards
if domain == "claude-code-plugin":
    queries += ["claude code plugin development best practices",
                "claude code hooks security patterns"]
if "public-api" in special_ctx:
    queries += ["REST API design standards OpenAPI 2026"]
if "handles-payments" in special_ctx:
    queries += ["PCI DSS compliance checklist developer"]
if "processes-pii" in special_ctx:
    queries += ["GDPR technical implementation checklist"]

# OSS + supply chain standards
queries += ["OpenSSF best practices scorecard criteria",
            "SLSA supply chain security levels",
            "{project_type} github stars:>100 architecture patterns"]
```

Run `WebSearch` for each query (cap at 15 queries to keep latency manageable).
Use `WebFetch` for high-value results to read the full document.

If a query fails → skip gracefully, note "Research unavailable for this query"
in the report section.

Synthesize into `external_standards_report`:
each dimension → list of `{standard, finding, severity}` items.

## Phase 4 — Synthesis

Cross-reference Phase 2 (internal) + Phase 3 (external findings):

- Finding present in both internal scan AND an external standard → bump
  severity one level (external validation = higher confidence)
- Deduplicate overlapping findings
- Score each dimension:
  - Start at 100
  - Critical: −15 each | High: −8 each | Medium: −3 each | Low: −1 each
  - Floor: 0
- Overall score = weighted average across active dimensions

## Phase 5 — Report + Backlog Selection

Print full report in this format:

```text
/zie-audit Report — <project> v<version>
<date> | Stack: <detected stack>

Overall Score: XX/100

  Security      XX  ████████░░
  Lean          XX  ████████░░
  Quality       XX  ████████░░
  Docs          XX  ████████░░
  Architecture  XX  ████████░░
  Performance   XX  ████████░░
  Dependencies  XX  ████████░░
  Developer Exp XX  ████████░░
  Standards     XX  ████████░░

Critical [N]  High [N]  Medium [N]  Low [N]

CRITICAL
(none | numbered findings)

HIGH
  1. [Dimension] Description
     → file:line | Effort: XS/S/M/L | Source: internal | <standard name>

MEDIUM / LOW
(same format — Low collapsed by default, shown with --show-low)

EXTERNAL STANDARDS GAP
  <Standard>: ✓ compliant | ⚠ gap: <summary>
```

Save full report to `zie-framework/evidence/audit-YYYY-MM-DD.md` regardless of
backlog selection (evidence/ is gitignored — local only).

Ask:

```text
Add to backlog: enter numbers (e.g. 1 3 7), "high" for all High+Critical,
"all" for everything, or "none" to skip
```

For each selected finding:

- Create `zie-framework/backlog/<slug>.md` with problem + motivation derived
  from the finding description
- Add to `zie-framework/ROADMAP.md` Next lane:
  `- [ ] <finding title> — [audit finding](backlog/<slug>.md)`

## Notes

- Always deep — no `--quick` mode; external research always runs
- `--focus <dim>`: scoped audit for one dimension (Phase 2 skips others;
  Phase 3 researches only that dimension, but deeply)
- Typical runtime: 3–8 minutes (parallel agents + web research)
- Not a replacement for `/zie-fix` (bug-focused) or release gates (pre-ship)
  — `/zie-audit` is periodic health review, run manually as needed
- Evidence saved to `zie-framework/evidence/` (gitignored, never committed)
