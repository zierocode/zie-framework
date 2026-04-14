---
approved: true
spec: specs/2026-04-14-sprint-context-passthrough-design.md
---

# Implementation Plan: Sprint Context Passthrough

## Overview

Create sprint context bundle (`.zie/sprint-context.json`) to carry specs and plans across sprint phases, eliminating redundant disk reads at phase boundaries.

## Tasks

### Phase 1: Context Bundle Creation

1. **Update `commands/sprint.md` Phase 1**
   - Add context bundle creation after spec + plan generation:
     ```python
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

2. **Update `commands/sprint.md` Phase 2 (implement)**
   - Read from bundle instead of disk:
     ```python
     context = json.loads(read_file(".zie/sprint-context.json"))
     item = next(i for i in context["items"] if i["slug"] == slug)
     spec_content = item["spec_content"]
     plan_content = item["plan_content"]
     ```
   - Add fallback to disk read if bundle missing (log warning)

3. **Update `commands/sprint.md` Phase 3 (release/retro)**
   - Use `roadmap_snapshot` from bundle for consistent state
   - Add fallback to disk read if bundle missing

### Phase 3: Testing

4. **Unit tests**
   - Verify bundle schema validation
   - Test bundle write/read round-trip

5. **Integration test**
   - Run sprint with 3 items
   - Verify context preserved across all phases
   - Verify no redundant disk reads

6. **Token audit**
   - Measure token savings vs baseline (target: ~4.5w tokens per 5-item sprint)

## Acceptance Criteria

- [ ] Context bundle written at end of Phase 1
- [ ] Phase 2 reads from bundle (not disk)
- [ ] Phase 3 uses `roadmap_snapshot` from bundle
- [ ] Fallback to disk read if bundle missing
- [ ] Context preserved across all phases
- [ ] Token savings measured (~4.5w per 5-item sprint)

## Estimated Effort

- Phase 1: ~1 hour
- Phase 2: ~1 hour
- Phase 3: ~1 hour
- **Total: ~3 hours**
