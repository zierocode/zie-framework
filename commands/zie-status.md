---
description: Show current SDLC state — active feature, ROADMAP summary, test health, and next suggested command.
allowed-tools: Read, Bash, Glob
---

# /zie-status — Show current SDLC state

Show a concise snapshot of where the project is right now. No LLM reasoning needed — just read files and print.

## Steps

1. **Check initialization**: if `zie-framework/` does not exist → print "Not initialized. Run /zie-init first." and stop.

2. **Read files**: `zie-framework/.config`, `zie-framework/ROADMAP.md`, `VERSION`, specs/plans dirs เพื่อ context

3. **Find active plan**: most recent file in `zie-framework/plans/` where ROADMAP.md "Now" section is not empty.

4. **Check test health**:
   - Check `.pytest_cache/v/cache/lastfailed`:
     - File exists and is **non-empty** (contains failed node IDs) → report `✗ fail`
     - File exists and is **empty** (last run had zero failures) → report `✓ pass`
     - If no `.pytest_cache/` directory at all → report `? stale`
   - Compare mtime of `.pytest_cache/` directory vs the newest file under `tests/`:
     - If any test file was modified more recently than `.pytest_cache/` → report `? stale`
     (A stale result overrides a prior pass/fail — if tests changed since the last run, the cached result is unreliable.)

5. **พิมพ์สถานะ** โดยใช้ markdown format:

   ## สถานะ zie-framework

   | | |
   | --- | --- |
   | โปรเจกต์ | \<directory name> (\<project_type>) |
   | Version | \<VERSION> |
   | Brain | \<enabled\|disabled> |

   **ROADMAP**
   - Now: \<N> in progress
   - Next: \<N> queued
   - Done: \<N> shipped

   **งานปัจจุบัน**: \<first Now item or "ยังไม่มีงาน">
   **Plan**: \<zie-framework/plans/latest.md or "ยังไม่มี plan">

   | Tests | สถานะ |
   | --- | --- |
   | unit | \<✓ pass \| ✗ fail \| ? stale \| n/a> |
   | integration | \<✓ pass \| ✗ fail \| ? stale \| n/a> |
   | e2e | \<✓ pass \| ✗ fail \| ? stale \| n/a> |

   **ขั้นตอนถัดไป**: \<context-appropriate suggestion>

6. **ตรรกะขั้นตอนถัดไป** (เลือกที่เกี่ยวข้องที่สุด):
   - Nothing in ROADMAP Now → "Start a feature: /zie-idea"
   - Active plan exists, tasks incomplete → "Continue: /zie-build"
   - Tests stale or failing → "Fix tests: /zie-fix"
   - All tasks in plan complete → "Ready to ship: /zie-ship"
   - Always available: "/zie-status | /zie-idea | /zie-build | /zie-fix | /zie-ship | /zie-retro"

## Notes

- Fast — no LLM, no network calls
- Safe to run anytime, even mid-session
