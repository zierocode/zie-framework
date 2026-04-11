---
approved: false
approved_at:
backlog:
---

# Context Window Health — Design Spec

**Problem:** The current 90% hard warning fires too late — by the time it appears, compaction options are limited and important context is already at risk. There is no early guidance on when or how to compact.

**Approach:** Add two earlier warning tiers (70%, 80%) to the existing context monitor, each with progressively stronger guidance. The 90% hard warning remains unchanged.

**Components:**
- `hooks/session-resume.py` or existing context monitor hook — extend with tiered thresholds

**Data Flow:**

Three-tier system:

| Tier | Threshold | Action |
|------|-----------|--------|
| 1 | 70% | Soft hint — "context filling up, consider compacting soon" |
| 2 | 80% | Recommendation — suggest compact now + explain what to save |
| 3 | 90% | Hard warning (existing behavior — no change) |

Tier 1 output (70%):
```
[zie-framework] Context at 70% — consider /compact soon to stay efficient
```

Tier 2 output (80%):
```
[zie-framework] Context at 80% — recommended: run /compact now.
Save any WIP notes to .remember/now.md before compacting.
```

Tier 3 (90%): existing hard warning — unchanged.

Each tier fires once per session (no repeated nagging). Session state tracks which tiers have fired.

**Error Handling:**
- Context % unavailable: skip tier check silently
- Session state write fails: tier may re-fire — acceptable, not critical
- Never blocks Claude

**Testing:**
- Unit: tier 1 fires at 70%, not before
- Unit: tier 2 fires at 80%, not before
- Unit: each tier fires only once per session
- Unit: tier 3 (90%) behavior unchanged from current implementation
- Unit: exits 0 when context % unavailable
