---
name: retro-format
description: Retrospective format and ADR structure for /zie-retro
type: reference
---

# Retro Format — zie-framework

## Retrospective Structure

Generate a retrospective with these sections. Keep each section concise — bullet points, not prose.

### What Shipped
List every feature, fix, or improvement that was completed. Include version if released.
```
- csv-export feature (v1.0.11) — memories now exportable as CSV, MD, JSON
- fix: hybrid search RRF scoring edge case with empty tags
```

### What Worked Well
Patterns, approaches, tools that saved time or reduced friction.
Only note things worth repeating — skip obvious basics.
```
- TDD cycle kept feature scope tight — no scope creep
- auto-test hook caught a regression in search.py within seconds
- zie-memory recalled the RRF pattern from a previous project
```

### What Was Painful
Friction points, unexpected complexity, things that slowed down.
Be specific — vague "communication" complaints are useless.
```
- SQLAlchemy async session management with LLM calls = complex (3-phase pattern)
- Playwright setup took longer than expected — browser install in CI
```

### Key Decisions Made
Decisions with lasting consequences — candidates for ADRs.
Each decision: what → why → consequence.
```
- Used HNSW LATERAL join for dedup instead of cross-join → O(n log n) vs O(n²)
- Split LLM calls from DB sessions → never hold connection during async LLM
```

### Patterns to Remember
Reusable techniques worth storing in the brain as P1/P2 memories.
```
- asyncpg CAST syntax: always CAST(:param AS vector), never :param::vector
- Pre-flight dedup in every write path prevents duplicates without extra API calls
```

## ADR Format

Only write an ADR when the decision:
1. Has lasting consequences (will affect future work)
2. Was non-obvious (could have gone a different way)
3. Someone might question later

**Template** (`zie-framework/decisions/ADR-NNN-slug.md`):
```markdown
# ADR-NNN: <Title — what was decided>

Date: YYYY-MM-DD
Status: Accepted

## Context
<1-3 sentences: what situation made this decision necessary>

## Decision
<1-3 sentences: exactly what was decided>

## Consequences
**Positive:** <what this enables or makes easier>
**Negative:** <what this makes harder or trades off>
**Neutral:** <things that change but are neither better nor worse>
```

**What does NOT need an ADR:**
- Routine implementation choices (which variable name, which loop style)
- Things that are easily reversible
- Library version choices (unless the version has breaking changes)
- Performance micro-optimizations

## Retrospective Frequency

| Trigger | Depth |
|---------|-------|
| After /zie-ship | Full retro + ADRs |
| After a major debugging session | Patterns only (no full retro) |
| End of long session (3+ hours) | Brief "what worked/what was painful" |
| Weekly (even without a release) | Light review of ROADMAP + brain |

## ROADMAP Update Checklist

After every retro, review ROADMAP.md:
- [ ] All shipped items moved to Done with date + version
- [ ] Next section re-prioritized based on learnings
- [ ] Any Icebox items that became relevant moved to Next
- [ ] New items discovered during the session added
- [ ] Remove items that are no longer relevant
