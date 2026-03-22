# Fork superpowers skills into zie-framework

zie-framework ปัจจุบัน depend on superpowers plugin สำหรับ brainstorming, TDD, writing-plans, systematic-debugging, และ dispatching-parallel-agents ทำให้เกิด friction เช่น directory structure conflicts, override notes ใน commands, และ zie-memory ไม่ integrate native

Fork skills เหล่านี้มาอยู่ใน `zie-framework/skills/` เพื่อให้ได้ version ที่ aware ของ zie-memory ทุก step, ใช้ directory structure ของ zie-framework by default, และไม่ต้อง depend on external plugin อีกต่อไป ผลลัพธ์คือ zie-framework เป็น self-contained SDLC framework ที่ทำงานได้สมบูรณ์โดยไม่ต้องมี superpowers

ref: zie-framework/specs/2026-03-22-sdlc-gate-enforcement-design.md (ดู zie-memory integration pattern)
