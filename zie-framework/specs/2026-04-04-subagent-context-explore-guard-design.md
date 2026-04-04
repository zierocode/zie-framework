# Spec: subagent-context — Skip Plan File Read for Explore Agents

**Slug:** `subagent-context-explore-guard`
**Date:** 2026-04-04
**Status:** Approved

## Problem

`subagent-context.py` reads the most-recent plan file on every SubagentStart event for
both Explore and Plan agents. Explore agents scanning for architecture patterns don't
act on the current incomplete task — only Plan agents need it. This fires repeatedly
during `/zie-implement` (which spawns multiple Explore agents) with zero benefit.

## Solution

Gate the plan file read behind an agent-type check. The hook already parses
`agentType` from the SubagentStart event in the outer guard. Extend that value down
into the inner operations block and skip the plan file read when `agentType` matches
`Explore` (case-insensitive).

The `additionalContext` emitted to Explore agents will still include `Active:` (feature
slug) and `ADRs:` count. The `Task:` field will be omitted entirely for Explore agents —
it adds noise without value.

## Acceptance Criteria

| # | Criterion |
| - | --------- |
| AC-1 | Plan agents receive `Active:`, `Task:`, and `ADRs:` in context (unchanged) |
| AC-2 | Explore agents receive `Active:` and `ADRs:` but NOT `Task:` |
| AC-3 | No plan file I/O occurs when `agentType` matches Explore |
| AC-4 | Hook exits 0 for both agent types with valid JSON on stdout |
| AC-5 | Non-matching agents (Task, Build, etc.) still produce no output (unchanged) |
| AC-6 | All existing guardrail and edge-case behaviours preserved |

## Out of Scope

- Changes to `hooks.json` matcher (`Explore|Plan` stays)
- Context payload format for Plan agents
- Any other hook

## Test Impact

Existing tests that assert `Task:` or plan-file content for `agentType: "Explore"` must
be updated to reflect the new behaviour (Explore omits `Task:`). New tests added for:
- Explore agent context contains `Active:` and `ADRs:` but not `Task:`
- Plan agent context still contains `Task:`
- Plan file read is skipped (validated by absence of `Task:` in Explore output)
