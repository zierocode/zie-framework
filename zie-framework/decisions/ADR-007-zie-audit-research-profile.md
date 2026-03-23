# ADR-007: /zie-audit — research_profile as Central Intelligence Layer

Date: 2026-03-23
Status: Accepted

## Context

Designing `/zie-audit` required a mechanism to make the 9-dimension analysis
and external research relevant to the specific project being audited — rather
than running the same fixed checks and queries against every codebase
regardless of language, framework, or domain.

## Decision

Phase 1 builds a `research_profile` struct by scanning manifests and source
files before any analysis begins. All downstream phases receive this struct
and use it to adapt their behavior:

- Phase 2 agents receive `research_profile` to run stack-aware checks (e.g.,
  Python-specific injection patterns, not generic shell checks)
- Phase 3 builds WebSearch queries dynamically from `research_profile.languages`,
  `.frameworks`, `.domain`, and `.special_ctx` — no hardcoded query lists

Additional principles baked in:

- **Always deep** — no `--quick` mode; external research always runs
- **Evidence local** — full report saved to `zie-framework/evidence/`
  (gitignored), never committed; keeps the repo clean
- **User selects backlog items** — audit produces findings; human decides
  what becomes a backlog item, not the command

## Consequences

- Audit output is meaningful across different project types without
  per-project customization
- Adding a new domain (e.g., `mobile-app`) only requires extending the query
  template in Phase 3 — not forking the command
- research_profile must be populated before Phase 2 starts — sequential
  dependency (Phase 1 is not parallelizable)
- evidence/ must be in `.gitignore` — enforced by `/zie-init` template
