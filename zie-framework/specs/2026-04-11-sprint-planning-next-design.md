---
approved: false
approved_at:
backlog:
---

# Sprint Planning (`/next`) — Design Spec

**Problem:** When backlog has multiple items, there is no structured way to decide what to work on next. Priority is implicit and easy to get wrong — important high-impact items get deferred while low-value tasks get picked arbitrarily.

**Approach:** `/next` command reads backlog items, ranks them by impact + dependency + age, and recommends top 3 with reasoning. If backlog is empty, suggests running `/brainstorm`.

**Components:**
- `commands/next.md` — new `/next` command

**Data Flow:**

1. Read all files in `zie-framework/backlog/`
2. Parse each item for: title, impact (high/medium/low if tagged), created date, dependencies
3. Filter out items already in progress (have matching spec with `approved: true`)
4. Score each item:
   - Impact: high=3, medium=2, low=1 (default: medium if untagged)
   - Age: +1 per week since created (older items get priority boost)
   - Dependency: items blocked by incomplete items scored down
5. Display top 3:

```
/next — recommended backlog items

1. [HIGH] conversation-capture
   Impact: bridges discuss→sprint gap (core workflow)
   Age: 3 days
   → Run: /spec conversation-capture

2. [MEDIUM] context-efficiency
   Impact: reduces token waste across all sessions
   Age: 1 day
   → Run: /spec context-efficiency

3. [MEDIUM] observability-health
   Impact: framework visibility + debugging
   Age: 1 day
   → Run: /spec observability-health
```

6. If backlog empty → "No backlog items. Run /brainstorm to discover what to build next."
7. If all items already in progress → "All backlog items are in progress. Run /rescue to check pipeline status."

**Error Handling:**
- Backlog item missing impact tag: default to medium
- Malformed backlog file: skip that item, continue with rest
- Always read-only, exits cleanly

**Testing:**
- Unit: high-impact items ranked above low-impact
- Unit: older items get priority boost over newer same-impact items
- Unit: in-progress items (approved spec exists) excluded from recommendations
- Unit: empty backlog shows brainstorm suggestion
- Unit: malformed backlog file skipped gracefully
