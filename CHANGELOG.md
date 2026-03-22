# Changelog

## v1.2.0 — 2026-03-23

### Features

- **6-stage SDLC pipeline** — replaced 3-stage (idea/build/ship) with
  backlog→spec→plan→implement→release→retro; single-responsibility commands
- **Reviewer quality gates** — `spec-reviewer`, `plan-reviewer`, `impl-reviewer`
  skills dispatch as subagents at each handoff (max 3 iterations → surface to human)
- **zie-init deep scan** — Agent(Explore) scan on existing projects populates
  PROJECT.md and project/* with real data instead of placeholder templates
- **Knowledge drift detection** — `knowledge_hash` stored at init/resync time;
  `/zie-status` warns when project files changed outside SDLC process
- **/zie-resync command** — manual trigger for full codebase rescan + doc update

### Fixes

- Remove all `superpowers_enabled` references — framework fully self-contained
- Fix markdownlint errors across all .md files; add pre-commit lint gate
- Update intent-detect hook for new pipeline command names

### Docs

- ADR D-006: Remove superpowers dependency
- ADR D-007: 6-stage SDLC pipeline with reviewer quality gates
- ADR-001: Reviewer skills as dispatched subagents
- ADR-002: markdownlint pre-commit gate

---

## v1.1.0 — 2026-03-22

### Features

- **Knowledge Architecture** — ทุก project ที่ใช้ zie-framework จะได้
  `PROJECT.md` (hub)
  และ `project/architecture.md`, `project/components.md`, `project/decisions.md`
  (spokes)
  สร้างอัตโนมัติตอน `/zie-init` จาก templates — ไม่ต้องเขียนเอง
- **Project Decisions log** — บันทึก architectural decisions แบบ append-only
  พร้อม
  status (Accepted / Superseded) — `/zie-retro` sync เข้า brain อัตโนมัติ

### Changed

- **Thai-primary commands** — ทุก `/zie-*` command และ skill ใช้ภาษาไทยเป็นหลัก
  สำหรับ instruction text, renamed phases เป็น intent-driven (เช่น "เขียน test
  ที่ล้มเหลวก่อน (RED)")
- **Batch release support** — `[x]` items ใน Now lane ค้างรอ release ได้หลาย
  features
  `/zie-ship` เป็นคนย้ายไป Done พร้อม version — ไม่ต้อง ship ทีละ feature
- **Intent-driven steps** — RED/GREEN/REFACTOR ใน `/zie-build` เป็น paragraph
  สั้น
  แทน bullet micro-steps; config reads collapsed เป็น 1 บรรทัด
- **Version bump suggestion** — `/zie-ship` วิเคราะห์ Now lane + git log แล้ว
  suggest
  major/minor/patch พร้อม reasoning ก่อนให้ confirm
- **Human-readable CHANGELOG** — `/zie-ship` draft entry ให้ approve ก่อน commit

### Tests

- 165 unit tests ครอบ commands, skills, hooks, templates (pytest)
