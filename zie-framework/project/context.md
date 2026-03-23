# Decisions — zie-framework

> Append-only — ไม่ลบ decisions เก่า ใช้ `Status: Superseded` แทน

---

## ADR-001: WIP=1 Rule

**Date:** 2026-03-22
**Status:** Accepted

**Context:** ต้องการให้ focus — หลาย feature พร้อมกันทำให้ context แตก และเพิ่ม
risk ของ merge conflicts

**Decision:** มีแค่ 1 `[ ]` (in-progress) feature ใน Now lane ต่อครั้ง `[x]`
(complete) items สามารถสะสมใน Now เพื่อ batch release

**Consequences:** developer ต้อง complete หรือ fix ก่อนเริ่ม feature ใหม่; ลด
WIP ในระบบ; รองรับ batch release โดยไม่ต้อง ship ทุก feature แยกกัน

---

## ADR-002: Graceful Degradation

**Date:** 2026-03-22
**Status:** Accepted

**Context:** zie-memory และ superpowers เป็น optional dependencies
ที่ไม่ใช่ทุกคนจะมี

**Decision:** ทุก feature ต้องทำงานได้โดยไม่มี optional deps — ใช้ `if
zie_memory_enabled:` guard เสมอ

**Consequences:** code มี conditional paths; แต่ผู้ใช้ที่ไม่มี deps
ก็ยังใช้งานได้ครบทุก command

---

## ADR-003: Hook Safety — Never Crash Claude

**Date:** 2026-03-22
**Status:** Accepted

**Context:** hooks ที่ crash จะทำให้ Claude Code ใช้ไม่ได้ทั้ง session

**Decision:** ทุก hook ต้องมี try/except ครอบทั้ง main() และ exit(0) เสมอเมื่อ
error — silent fail ดีกว่า crash

**Consequences:** bugs ใน hooks อาจ silent fail; ต้องมี logging ที่ดีเพื่อ
debug; pytest unit tests ครอบทุก hook

---

## ADR-004: Native Skills แทน Superpowers Dependency

**Date:** 2026-03-22
**Status:** Accepted

**Context:** zie-framework ขึ้นกับ superpowers:brainstorming,
superpowers:writing-plans ซึ่งเป็น external dependency

**Decision:** fork skills ที่ใช้บ่อยมาไว้ใน `zie-framework/skills/` โดยตรง
(spec-design, write-plan, debug, verify, tdd-loop, test-pyramid, retro-format)

**Consequences:** ต้อง maintain skills เอง; แต่ได้ independence + customization
สำหรับ zie-framework context

---

## ADR-005: Batch Release Pattern

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Solo developer workflow — ไม่จำเป็นต้อง ship ทุก feature แยกกัน;
อยากสะสม features แล้ว release พร้อมกัน

**Decision:** `[x]` items ใน Now = "complete, pending release" — ค้างไว้จนกว่า
/zie-release จะย้ายทั้งหมดไป Done พร้อม version; /zie-implement ไม่ย้าย items
ไป Done

**Consequences:** Now lane อาจมีหลาย `[x]` items; Done = shipped จริง;
/zie-release batch-moves ทั้งหมดพร้อมกัน

---

## ADR-007: 6-stage SDLC pipeline with reviewer quality gates (2026-03-23)

**Date:** 2026-03-23
**Status:** Accepted

**Context:** The original pipeline had 3 commands doing too much each:
`/zie-idea` (brainstorm + spec + plan), `/zie-build` (implement), `/zie-ship`
(release). There were no quality gates between stages — a spec could proceed
to implementation without review, and code could ship without per-task review.

**Decision:** Redesign to a 6-stage pipeline with single-responsibility
commands and automatic reviewer quality gates at each handoff:

1. `/zie-backlog` — capture problem + motivation only
2. `/zie-spec` → spec-design → **spec-reviewer loop** (max 3 iter)
3. `/zie-plan` → write-plan → **plan-reviewer loop** (max 3 iter)
4. `/zie-implement` → TDD per task → **impl-reviewer after each REFACTOR**
5. `/zie-release` — full gate sequence → merge → tag
6. `/zie-retro` — ADRs + brain storage

Old commands (zie-idea, zie-build, zie-ship) deleted. Intent-detect and
session-resume hooks updated to new names.

**Consequences:** Every spec, plan, and implementation task now goes through
an automatic quality check before proceeding. Reviewer loops surface issues
early rather than at release time. Backward compatibility: existing `.config`
files unchanged; any project using old commands must update to new names.

---

## ADR-006: Remove superpowers dependency (2026-03-23)

**Date:** 2026-03-23
**Status:** Accepted

**Context:** zie-framework previously used superpowers:brainstorming,
superpowers:writing-plans, superpowers:systematic-debugging, and
superpowers:verification-before-completion. These were forked into
zie-framework/skills/ as spec-design, write-plan, debug, and verify (D-004).
The last remaining references (`superpowers_enabled` config key in
zie-plan.md, zie-init.md, and session-resume.py hook) were not cleaned up
at the time of the fork.

**Decision:** zie-framework is fully self-contained. Remove all
`superpowers_enabled` references from commands and hooks. Remove
superpowers from the optional dependencies list in docs.

**Consequences:** zie-framework no longer depends on the superpowers plugin
in any form. The `superpowers_enabled` field in existing `.config` files is
silently ignored (backward compatible — no migration needed).

---

## ADR-008: Hybrid Release — SDLC Gates + Project-Defined Publish (ADR-005)

**Date:** 2026-03-23
**Status:** Accepted

**Context:** `/zie-release` previously did git ops directly, making it
impossible for projects with custom publish steps to integrate properly.

**Decision:** Split into SDLC layer (`/zie-release` — gates + VERSION +
CHANGELOG + ROADMAP commit) and project layer (`make release NEW=<v>` — git
merge, tag, push, project-specific publish). Makefile templates ship a
`ZIE-NOT-READY` skeleton; `/zie-init` negotiates the skeleton on first run.

**Consequences:** Projects must implement `make release` before first
release. All git ops live in `make release`. SDLC layer is portable; publish
layer is project-specific.

---

## ADR-010: /zie-audit uses research_profile as dynamic intelligence layer (ADR-007)

**Date:** 2026-03-23
**Status:** Accepted

**Context:** Audit checks and external research queries needed to adapt to the
specific project's stack and domain — fixed checks produce irrelevant noise.

**Decision:** Phase 1 builds `research_profile` (languages, frameworks, domain,
deps, special_ctx) from manifests. All downstream phases use it to run
stack-aware checks and build WebSearch queries dynamically. Always-deep, no
quick mode. Evidence saved locally (gitignored). Human selects which findings
become backlog items.

**Consequences:** Audit is generically useful across project types. Adding a
new domain only requires extending the Phase 3 query template. Phase 1 is a
sequential prerequisite — not parallelizable.

---

## ADR-009: Reviewer Phase 1/2/3 with Context Bundles (ADR-006)

**Date:** 2026-03-23
**Status:** Accepted

**Context:** Reviewers previously reviewed docs in isolation — no
cross-referencing against actual files, ADR history, or ROADMAP.

**Decision:** All three reviewer skills (spec/plan/impl) load a context
bundle before reviewing (Phase 1: named files + ADRs + context.md + ROADMAP),
run the existing checklist (Phase 2), then do cross-reference checks (Phase 3:
file existence, ADR conflict, ROADMAP conflict, pattern match). `impl-reviewer`
omits ROADMAP conflict check. Graceful skip if any source is missing.

**Consequences:** Reviewers catch real-world issues. Bundle adds latency per
review. Phase 3 list numbering restarts at 1 per phase (markdownlint MD029).
