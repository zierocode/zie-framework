# ADR-029: Use General-Purpose Agent for Subagents in zie-retro and zie-release

Date: 2026-03-30
Status: Accepted

## Context

zie-retro and zie-release previously invoked plugin-specific subagent types. This required the plugin to be loaded in the subprocess session, which caused failures when the marketplace cache was stale or missing.

## Decision

zie-retro and zie-release now spawn general-purpose agents (no plugin-specific agent type). All required context and instructions are passed inline, making each subprocess session self-contained.

## Consequences

**Positive:** Subagent sessions no longer depend on plugin cache state; eliminates a class of stale-cache failures.
**Negative:** Future agents that need plugin skills (slash commands, hooks) cannot use this pattern and require a separate invocation path.
**Neutral:** Session bootstrap instructions must now carry any context previously sourced from the plugin.
