# Backlog: Eliminate subagent-context overhead when idle + split Explore/Plan matchers

**Problem:**
subagent-context.py fires for all Explore and Plan subagents even when no task is
active. When `active_task == "none"` and `feature_slug == "none"`, the emitted
payload is `[zie-framework] Active: none | ADRs: N` — near-zero signal that costs
a Python startup + ROADMAP read (cached but still a cache hit) + context.md read
on every subagent start.

Additionally, the `"Explore|Plan"` matcher causes Explore subagents to trigger the
plans/ glob scan (to find the current plan file) even though Explore agents never
use the plan context — the plan-file scan is gated on `re.search(r'Plan', agent_type)`
but the glob still runs for both.

**Motivation:**
Eliminating no-op injections reduces subagent context overhead by ~50–100 tokens per
subagent when idle. Splitting the matcher avoids a plans/ glob for Explore agents,
which is the most expensive I/O path in this hook.

**Rough scope:**
- Add early exit in subagent-context.py: if `active_task == "none"` → sys.exit(0)
- Split hooks.json SubagentStart into two entries:
  - `"Explore"` matcher → emits only feature slug + ADR count (no plans/ glob)
  - `"Plan"` matcher → emits full context including plan task
- Tests: Explore agent with no active task → no context injected;
         Plan agent → gets full context
