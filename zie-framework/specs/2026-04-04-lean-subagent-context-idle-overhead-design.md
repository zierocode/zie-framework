---
approved: true
approved_at: 2026-04-04
backlog: zie-framework/backlog/lean-subagent-context-idle-overhead.md
---

# Lean Subagent Context — Design Spec

**Problem:** `subagent-context.py` fires for all Explore and Plan subagents even when no task is active, emitting near-zero-signal payloads (`Active: none | ADRs: N`) that still cost a Python startup, a ROADMAP cache hit, and a context.md read per subagent spawn. Additionally, the combined `"Explore|Plan"` matcher in hooks.json causes both agent types to enter the same hook entry, even though Explore agents never use the plans/ glob path (already guarded by ADR-046) — and the matcher coupling makes the per-type cost profile opaque.

**Approach:** Two changes in tandem:

1. **Idle early-exit** — After the ROADMAP read, if `active_task == "none"` (Now lane is empty), call `sys.exit(0)` immediately. This eliminates the context.md ADR-count read and the `print(json.dumps(...))` call for the common idle state. Applies to both Explore and Plan agents.

2. **Split hooks.json matchers** — Replace the single `"Explore|Plan"` SubagentStart entry with two separate entries: one with matcher `"Explore"` and one with matcher `"Plan"`, both pointing to the same `subagent-context.py` script. This makes the routing explicit, allows independent future evolution (e.g., different timeouts or flags per agent type), and documents in hooks.json that the two agent types have different behavior.

**Components:**

- `hooks/subagent-context.py` — add idle early-exit after ROADMAP read (one guard block)
- `hooks/hooks.json` — split SubagentStart from one entry (`"Explore|Plan"`) into two entries (`"Explore"` and `"Plan"`)
- `tests/unit/test_hooks_subagent_context.py` — add test: Explore with no active task → no output; Plan with no active task → no output; existing matcher test updated to assert two entries
- `tests/unit/test_hooks_json.py` — update SubagentStart matcher assertion if it checks the combined pattern

**Data Flow:**

1. SubagentStart event fires → hooks.json routes to `subagent-context.py` via `"Explore"` or `"Plan"` matcher
2. Outer guard: parse event, check `agentType`, check `zie-framework/` dir exists — unchanged
3. ROADMAP read (cached): extract `feature_slug` and set `active_task` from Now lane
4. **NEW:** If `feature_slug == "none"` (Now lane empty) → `sys.exit(0)` — no ADR read, no JSON output
5. If `feature_slug != "none"` and agent is Plan → plans/ glob + task extraction (existing ADR-046 guard)
6. ADR count read from `context.md`
7. Emit `additionalContext` JSON payload

**Edge Cases:**

- `feature_slug == "none"` with a non-empty Now lane that parsed to empty string — guard checks `feature_slug == "none"` post-parse, not raw Now content, so this is safe
- Cache miss on ROADMAP read when idle → disk read still occurs before exit; this is acceptable (cache miss is already the slow path)
- Plan agent with `feature_slug != "none"` but no plan files → exits normally, `active_task = "unknown"` — unchanged behavior
- Two hooks.json entries for SubagentStart: hooks fire once each per matched agent type — verified by existing Claude Code behavior (matcher is per-entry, not per-event)
- Tests asserting `"Explore|Plan"` combined matcher must be updated to assert two separate entries

**Out of Scope:**

- Splitting subagent-context.py into two scripts (over-engineering; ADR-046 already gates plan-file I/O cleanly)
- Caching the ADR count (separate concern; context.md read is fast)
- Suppressing output for Plan agents in idle state when `feature_slug != "none"` (they have real context to inject)
- Changing the payload format or fields for active-task cases
