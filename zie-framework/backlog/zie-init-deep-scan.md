# zie-init Deep Scan + Knowledge Drift Detection

## Problem

`/zie-init` บน existing project สร้าง `PROJECT.md` และ `project/*` จาก
template placeholder — ไม่ได้สะท้อน codebase จริง ทำให้ knowledge docs
ไม่มีประโยชน์ตั้งแต่วันแรก

นอกจากนี้ เมื่อ codebase เปลี่ยนไป (เพิ่ม module, dependency ใหม่) ไม่มี
mechanism ตรวจจับว่า knowledge docs ล้าสมัยแล้ว

## Goal

`/zie-init` บน existing project ต้องให้ผล **เทียบเท่ากับการใช้ zie-framework
ตั้งแต่วันแรก** — knowledge docs ถูกต้อง ครบถ้วน สะท้อนสถานะจริงของ
codebase ณ ปัจจุบัน

## Scope

1. **Deep scan at init time** — ตรวจจับ existing vs greenfield project แล้ว
   invoke `Agent(subagent_type=Explore)` scan codebase ทั้งหมด → draft
   `PROJECT.md` + `project/*` จาก scan report → user confirm ก่อน write
2. **Knowledge hash** — คำนวณ SHA-256 hash จาก directory tree + file counts
   + key config files → เก็บใน `zie-framework/.config`
3. **Drift detection** — `/zie-status` recompute hash เปรียบเทียบกับ baseline
   → แจ้งเตือนถ้า drift
4. **Resync** — `/zie-resync` command ใหม่: full scan → draft → confirm →
   write → update hash

## Spec

ดู `specs/2026-03-23-zie-init-deep-scan-design.md` สำหรับ design ที่
approved แล้ว
