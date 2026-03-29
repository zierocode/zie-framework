# zie-audit-v2

## Problem

`/zie-audit` covers only 3 dimensions (Security, Code Health, Structural) and
has no dedicated external research pass. Findings overlap across agents with
wasted WebSearch budget, Phase 3 synthesis requires an extra agent call, and
Phase 4 backlog integration prompts one finding at a time. The scoring scheme
(1–10 × 1–10) produces ambiguous ranks with no "Quick Win" identification.

## Motivation

An audit tool should do two distinct jobs: find what's broken AND discover
what's missing. The current design only does the first. Teams using zie-framework
on any stack miss ecosystem-specific improvement opportunities that a targeted
external research pass would surface. The tool should be applicable to any
project type (Python, TypeScript, Go, etc.) without hardcoded assumptions.

## Rough Scope

- Add External Research agent (stack/domain-driven WebSearch, improvement framing)
- Add Dependency Health, Performance, Observability dimensions
- Phase 1: include ROADMAP/ADR dedup context + git log
- Phase 3: inline synthesis instead of separate agent (saves 1 agent call)
- Phase 4: batch backlog prompts (all/select/skip)
- Scoring: Quick Win / Strategic / Defer matrix
- Generic: all research variables driven by detected {stack}/{domain}
