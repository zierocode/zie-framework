# ADR-032: Shared Context Bundle Built Once in Phase 1 of zie-audit

Date: 2026-03-30
Status: Accepted

## Context

zie-audit Phase 2 spawns multiple parallel analysis agents. Previously, each agent independently reconstructed the same project context (file tree, CLAUDE.md, component map), resulting in redundant work and the risk of inconsistent views if any file changed between agent starts.

## Decision

zie-audit Phase 1 builds a shared_context bundle once and passes it to all Phase 2 agents as a pre-built payload. Phase 2 agents consume the bundle rather than reconstructing context themselves.

## Consequences

**Positive:** Phase 2 agents start faster and operate on a guaranteed-consistent context snapshot.
**Negative:** Phase 1 is a hard blocking dependency — Phase 2 cannot begin until Phase 1 completes. A bug in Phase 1 context assembly propagates to all Phase 2 agents.
**Neutral:** shared_context schema must be versioned if Phase 2 agent expectations diverge in future iterations.
