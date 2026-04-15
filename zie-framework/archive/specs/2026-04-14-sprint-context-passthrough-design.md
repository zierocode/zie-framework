---
approved: true
backlog: backlog/sprint-context-passthrough.md
---

# Sprint Context Passthrough — Design Specification

## Summary

Introduce a sprint context bundle (`.zie/sprint-context.json`) that carries specs and plans across sprint phases, eliminating redundant disk reads and context re-parsing at phase boundaries.

## Problem Statement

Current sprint execution has three phase boundaries where context is lost:
- **Phase 1** (spec/plan): Skill calls spawn independently, each re-reading approved plans from disk
- **Phase 2** (implement): `make zie-implement` subprocess loses in-session cache
- **Phase 3** (release/retro): ROADMAP re-parsed multiple times

Result: ~4.5w tokens wasted per 5-item sprint; ROADMAP re-parsed 3×.

## Goals

| Goal | Success Metric |
|------|----------------|
| Eliminate redundant disk reads | Context loaded once at sprint start |
| Preserve context across phases | Phase 2/3 read from bundle, not disk |
| Reduce token waste | Save ~4.5w tokens per 5-item sprint |

## Non-Goals

- Changing individual item context structure
- Modifying the unified-context-cache (depends on it, doesn't change it)

## Design

### Context Bundle Schema

`.zie/sprint-context.json`:
```json
{
  "sprint_id": "2026-04-14",
  "created_at": "2026-04-14T09:00:00Z",
  "items": [
    {
      "slug": "feature-slug",
      "spec_path": "zie-framework/specs/2026-04-14-feature-slug-design.md",
      "spec_content": "<full markdown content>",
      "plan_path": "zie-framework/plans/2026-04-14-feature-slug-plan.md",
      "plan_content": "<full markdown content>"
    }
  ],
  "roadmap_snapshot": "<ROADMAP.md content at sprint start>"
}
```

### Phase 1: Context Bundle Creation

`commands/sprint.md` Phase 1 writes the bundle after generating specs and plans:

```python
# After spec + plan generation for each item
context_bundle = {
    "sprint_id": datetime.now().strftime("%Y-%m-%d"),
    "created_at": datetime.now().isoformat() + "Z",
    "items": [],
    "roadmap_snapshot": read_file("zie-framework/ROADMAP.md")
}

for item in sprint_items:
    context_bundle["items"].append({
        "slug": item.slug,
        "spec_path": item.spec_path,
        "spec_content": read_file(item.spec_path),
        "plan_path": item.plan_path,
        "plan_content": read_file(item.plan_path)
    })

write_file(".zie/sprint-context.json", json.dumps(context_bundle, indent=2))
```

### Phase 2: Context Bundle Consumption

`commands/sprint.md` Phase 2 reads from bundle instead of disk:

```python
# Before: read from disk
spec_content = read_file(spec_path)
plan_content = read_file(plan_path)

# After: read from bundle
context = json.loads(read_file(".zie/sprint-context.json"))
item = next(i for i in context["items"] if i["slug"] == slug)
spec_content = item["spec_content"]
plan_content = item["plan_content"]
```

### Phase 3: Release/Retro Context

Phase 3 uses `roadmap_snapshot` from bundle for consistent state:

```python
context = json.loads(read_file(".zie/sprint-context.json"))
roadmap_content = context["roadmap_snapshot"]
```

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `.zie/sprint-context.json` | New (runtime) | Sprint context bundle |
| `commands/sprint.md` | Modify | Write bundle Phase 1; read Phase 2/3 |

## Dependencies

- **unified-context-cache**: Required (ADR pending)
- No changes to existing context cache structure

## Testing Plan

1. **Unit**: Verify bundle schema validation
2. **Integration**: Sprint with 3 items — verify context preserved across phases
3. **Token audit**: Measure token savings vs baseline

## Rollout Plan

1. Add bundle write to `sprint.md` Phase 1
2. Add bundle read to Phase 2/3
3. Test with 3-item sprint
4. Measure token savings

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Bundle grows large | Only include items in current sprint |
| Stale roadmap snapshot | Snapshot is intentional — captures sprint-start state |
| Bundle missing | Fall back to disk read (log warning) |

## Open Questions

None — scope is well-defined.
