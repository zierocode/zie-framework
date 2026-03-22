# Changelog

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
