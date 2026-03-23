---
approved: true
approved_at: 2026-03-23
backlog: backlog/zie-audit.md
---

# /zie-audit — Design Spec

**Problem:** No systematic way to audit a project across all quality dimensions
using both internal analysis and live external standards research.

**Approach:** A 5-phase command. Phase 1 detects the project and builds a
`research_profile` struct. Phase 2 spawns 5 parallel internal analysis agents
(one per dimension group). Phase 3 runs a research agent that builds and
executes WebSearch/WebFetch queries dynamically from `research_profile` — not
hardcoded. Phase 4 synthesizes and scores. Phase 5 presents a scored report and
creates backlog items for selected findings.

**Components:**

- `commands/zie-audit.md` — new command (5 phases inline, no new skills needed)
- `tests/unit/test_zie_audit.py` — content validation tests
- `zie-framework/project/components.md` — add /zie-audit to Commands table

**Data Flow:**

```
/zie-audit [--focus <dimension>]

Phase 1 — Project Intelligence
  Read .config, detect stack/deps/domain/deployment/special context
  Output: research_profile {languages, frameworks, domain, deps,
          project_type, test_runner, has_frontend, deployment, special_ctx}

Phase 2 — Parallel Internal Analysis (5 agents, each gets research_profile)
  Agent A: Security   — secrets, injection, auth, input validation, CVE hints
  Agent B: Lean       — dead code, duplication, over-engineering, unused deps
  Agent C: Quality    — test coverage, fragile tests, missing edge cases, TODOs
  Agent D: Docs       — stale refs, missing docs, broken examples, README gaps
  Agent E: Architecture — coupling, SRP, inconsistent patterns, error handling
  (Performance, Dep Health, DX, Standards run as sub-checks within agents)

Phase 3 — Dynamic External Research (1 agent)
  Build queries from research_profile:
    - language/runtime standards (PEP, TC39, Go spec, ...)
    - framework-specific security guides
    - OWASP for detected stack
    - domain-specific standards (PCI if payments, GDPR if PII, OpenAPI if API)
    - OSS standards (OpenSSF, SLSA, conventional commits, semver)
    - community patterns (GitHub search for similar projects)
  WebSearch + WebFetch for each query (max 15 queries)
  Output: external_standards_report {dimension → [{standard, finding, severity}]}

Phase 4 — Synthesis
  Cross-reference Phase 2 + Phase 3
  Finding in both → severity bump (+1 level)
  Score per dimension: 100 − (Critical×15 + High×8 + Medium×3 + Low×1), min 0
  Overall = weighted average

Phase 5 — Report + Backlog Selection
  Print scored report (see format in spec)
  Save to zie-framework/evidence/audit-YYYY-MM-DD.md (gitignored, always)
  Ask: "Add to backlog: numbers / 'high' / 'all' / 'none'"
  Create backlog/<slug>.md for selected findings
  Add to ROADMAP Next lane
```

**Report Format:**

```text
/zie-audit Report — <project> v<version>
<date> | Stack: <detected>

Overall Score: XX/100

  Security      XX  <bar>
  Lean          XX  <bar>
  Quality       XX  <bar>
  Docs          XX  <bar>
  Architecture  XX  <bar>
  Performance   XX  <bar>
  Dependencies  XX  <bar>
  Developer Exp XX  <bar>
  Standards     XX  <bar>

Critical [N]  High [N]  Medium [N]  Low [N]

CRITICAL / HIGH / MEDIUM / LOW sections with findings numbered
(each: dimension, description, file:line or "per <standard>", effort XS/S/M/L)

EXTERNAL STANDARDS GAP
  <Standard>: ✓ compliant | ⚠ gap: <summary>

---
Add to backlog: numbers, "high", "all", or "none"
```

**Edge Cases:**

- `--focus <dim>` → skip other dimensions in Phase 2; still research that
  dimension in Phase 3 but targeted only
- WebSearch/WebFetch failure → graceful skip, note "Research unavailable for
  this query" in report
- No dependencies detected → skip dep health sub-check, note in report
- All findings selected → create backlog items in batch
- No findings → print "No issues found" with score summary, still save evidence

**Out of Scope:**

- Auto-fixing issues
- Scheduling or automated runs
- Historical trend tracking
- CI/CD integration
- Multi-project comparison
- Scoring normalization across different project types
