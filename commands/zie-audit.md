---
description: Deep project audit — 9-dimension analysis with external research. Produces scored findings for backlog.
allowed-tools: Read, Bash, Glob, Grep, Skill, Agent, WebSearch, WebFetch
model: opus
effort: high
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

Print: `[Phase 1/5] Project Intelligence`

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

### Hard Data Collection

Before spawning agents, run toolchain instrumentation to produce hard numbers.
Store results in `hard_data` and pass to relevant agents in Phase 2.

```text
hard_data = {
  coverage_report: "",   # pytest --cov stdout (% per module)
  complexity_report: "", # radon cc -s stdout (cyclomatic complexity per file)
  vuln_report: "",       # pip audit / npm audit stdout (CVE list)
}
```

Run each command if the tool is present; skip gracefully with a note if unavailable:

- **Coverage** (Python): `pytest --cov --cov-report=term-missing -q`
  - If pytest or coverage not installed → set `hard_data.coverage_report = "unavailable"`
- **Complexity** (Python): `radon cc -s -a .`
  - If radon not installed → set `hard_data.complexity_report = "unavailable"`
- **Vulnerabilities**:
  - Python: `pip audit` (if pip-audit installed)
  - Node: `npm audit --json` (if package.json present)
  - If neither available → set `hard_data.vuln_report = "unavailable"`

Pass `hard_data.coverage_report` and `hard_data.complexity_report` to Agent C
context. Pass `hard_data.vuln_report` to Agent A context. Agents must use these
numbers directly in their findings rather than estimating from code patterns.

## Phase 2 — Parallel Internal Analysis

Print: `[Phase 2/5] Parallel Internal Analysis`

Spawn 5 parallel agents via `Agent` tool. Each receives `research_profile` and
full codebase access. Each returns a findings list:
`[{severity, dimension, description, location, effort}]`
As each agent returns, print: `  Agent {X} ({Domain}) ✓`

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

Print: `[Phase 3/5] Dynamic External Research`

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

# Dependency version-specific queries (first 10 deps from manifest)
top_deps = first 10 entries from research_profile.deps
for each <dep>, <version> in top_deps:
    if <version> is not empty:
        add "{dep} {version} CVE" to queries
        add "{dep} {version} security vulnerability" to queries
```

Cap the query list at 25 entries. Then dispatch **all** WebSearch calls in a
single parallel batch — do not loop sequentially. Collect results into a dict
keyed by query string. Before the batch, print: `[Phase 3/5] Dynamic External
Research — dispatching {N} queries in parallel`.

If any individual query fails → record "Research unavailable" for that query
and continue; do not abort the batch.

After the parallel batch completes, use `WebFetch` sequentially for any
high-value URLs returned by the search results (WebFetch depends on search
output so it remains sequential).

Synthesize into `external_standards_report`:
each dimension → list of `{standard, finding, severity}` items.

## Phase 4 — Synthesis

Print: `[Phase 4/5] Synthesis`

Cross-reference Phase 2 (internal) + Phase 3 (external findings):

- Finding present in both internal scan AND an external standard → bump
  severity one level (external validation = higher confidence)
- Deduplicate overlapping findings
- Score each dimension:
  - Start at 100
  - Critical: −15 each | High: −8 each | Medium: −3 each | Low: −1 each
  - Floor: 0
- Overall score = weighted average across active dimensions

## Historical Diff — Since Last Audit

After scoring, compare against the most recent previous audit:

1. Glob `zie-framework/evidence/audit-*.md` sorted descending by filename date.
2. If no previous audit file exists → skip this section entirely; proceed to Phase 5.
3. Parse the previous report's dimension score table (lines matching
   `  <Dimension>  XX`) to extract last scores.
4. For each active dimension compute delta: `current_score − last_score`.
5. Prepend the following section to the Phase 5 report, immediately after the
   Overall Score line:

```text
Since last audit (<YYYY-MM-DD>)

  Security      +N / -N  (was XX → now XX)
  Lean          +N / -N  (was XX → now XX)
  Quality       +N / -N  (was XX → now XX)
  Docs          +N / -N  (was XX → now XX)
  Architecture  +N / -N  (was XX → now XX)
  ...

Improved: N dimensions  |  Regressed: N dimensions  |  Unchanged: N
```

If parsing fails for any dimension (format mismatch) → show "N/A" for that row.
Never block Phase 5 due to historical diff errors.

## Phase 5 — Report + Backlog Selection

Print: `[Phase 5/5] Report + Backlog Selection`

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

### Auto-Fix Offer

After writing backlog items, scan the selected findings for auto-fixable candidates:

```text
auto_fixable = [f for f in selected_findings
                if f.severity in ("Low", "Medium")
                and f.get("auto-fixable") is True]
```

- If `auto_fixable` is empty → skip this section entirely.
- High and Critical findings are never offered for auto-fix — they require
  deliberate SDLC treatment.

For each qualifying finding, present:

```text
Auto-fix available: [Dimension] <description> (Low/Medium)
Apply fix now? (y/n)
```

On "y":
- Invoke `/zie-fix` with the finding description and file location as context.
- Report result ("Fixed" or "Needs manual review") before offering the next item.

On "n" → skip to the next item.

After all items are processed (or skipped), close the audit session normally.

Print: `5/5 phases complete.`

## Notes

- Always deep — no `--quick` mode; external research always runs
- `--focus <dim>`: scoped audit for one dimension (Phase 2 skips others;
  Phase 3 researches only that dimension, but deeply)
- Typical runtime: 3–8 minutes (parallel agents + web research)
- Not a replacement for `/zie-fix` (bug-focused) or release gates (pre-ship)
  — `/zie-audit` is periodic health review, run manually as needed
- Evidence saved to `zie-framework/evidence/` (gitignored, never committed)
