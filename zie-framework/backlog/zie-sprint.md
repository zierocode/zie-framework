# zie-sprint — Sprint Clear Command

## Problem

วิธีปัจจุบัน ซี process backlog items ทีละอัน ผ่าน spec → plan → implement → release → retro
ปัญหา: ทุก stage ทำซ้ำซ้อน (context loads, test gates, release ceremony, retro) N ครั้ง
Result: N items = N releases, N retros, ~25 context loads

## Motivation

Build `/zie-sprint` — single command ที่ orchestrate full pipeline สำหรับ **all backlog items at once** ด้วย phase parallelism:

- **Phase 1** (SPEC all): parallel agents per item
- **Phase 2** (PLAN all): `/zie-plan slug1 slug2 ...` (already parallel)
- **Phase 3** (IMPLEMENT): sequential WIP=1, pipeline stream warm-up
- **Phase 4** (RELEASE): single batch release for all items
- **Phase 5** (RETRO): single sprint retro

**Throughput gains**:
- Wall-clock: ~(N-1)× faster spec + plan phases
- Context loads: N×25 → 1×1 (reuse context_bundle)
- Release ceremony: N → 1
- Git merges: N → 1
- Test gates: N → 1 batch

เป็น **force multiplier** สำหรับ sprint clearing.

## Rough Scope

**In**:
- Audit step: classify all items (next/ready/now/done)
- Phase 1: spec all items (parallel, --draft-plan)
- Phase 2: plan all items (parallel)
- Phase 3: impl all items (sequential WIP=1, pipeline stream)
- Phase 4: batch release (single version bump, merge, tag)
- Phase 5: sprint retro (all items, single ADR session)
- Dependency detection (respects `<!-- depends_on: slug -->`)
- Dry-run mode
- Version override flag
- Context bundle (load once, pass everywhere)

**Out**:
- Individual spec/plan/impl/release — users can still run these separately
- Cross-sprint dependencies
- Backlog refactoring
