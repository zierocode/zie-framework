---
description: Show current SDLC state — active feature, ROADMAP summary, test health, and next suggested command.
allowed-tools: Read, Bash, Glob
---

# /zie-status — Show current SDLC state

Show a concise snapshot of where the project is right now. No LLM reasoning
needed — just read files and print.

## Steps

**Live context (injected at command load):**

ROADMAP snapshot (first 30 lines):
!`cat zie-framework/ROADMAP.md | head -30`

Knowledge hash:
!`python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"`

1. **Check initialization**: if `zie-framework/` does not exist → print "Not
   initialized. Run /zie-init first." and stop.

2. **Read files**: `zie-framework/.config` (including `knowledge_hash`,
   `knowledge_synced_at`), `zie-framework/ROADMAP.md`,
   `VERSION`, specs/plans dirs เพื่อ context

3. **Find active plan**: most recent file in `zie-framework/plans/` where
   ROADMAP.md "Now" section is not empty.

4. **Check knowledge drift** via Bash — must use the **same algorithm**
   as `/zie-resync` and `/zie-init`:

   ```bash
   python3 hooks/knowledge-hash.py
   ```

   - Read `knowledge_hash` from `zie-framework/.config`
   - If missing → Knowledge status: `? no baseline — run /zie-resync`
   - Compare script output to stored hash:
     - Equal → `✓ synced (<knowledge_synced_at>)`
     - Differs → `⚠ drift detected — run /zie-resync`
   - Knowledge row is informational only — does not block suggestions

5. **Check test health** (detect test runner from `.config`):

   **pytest** (`test_runner=pytest`):
   - Check `.pytest_cache/v/cache/lastfailed`:
     - Non-empty → `✗ fail` | Empty → `✓ pass` | No dir → `? stale`
   - Compare mtime of `.pytest_cache/` vs newest file under `tests/`:
     - Newer test file → `? stale` (overrides prior result)

   **vitest/jest** (`test_runner=vitest|jest`):
   - Check `node_modules/.vitest/` or `.jest-cache/` last-run timestamp
   - If no cache dir → `? stale`

6. **พิมพ์สถานะ** โดยใช้ markdown format:

   ## สถานะ zie-framework

   | | |
   | --- | --- |
   | โปรเจกต์ | \<directory name> (\<project_type>) |
   | Version | \<VERSION> |
   | Brain | \<enabled\|disabled> |
   | Knowledge | \<✓ synced (date) \| ⚠ drift: /zie-resync \| ? no baseline> |

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

7. **ตรรกะขั้นตอนถัดไป** (เลือกที่เกี่ยวข้องที่สุด):
   - Nothing in ROADMAP Now → "Start a feature: /zie-backlog"
   - Active plan exists, tasks incomplete → "Continue: /zie-implement"
   - Tests stale or failing → "Fix tests: /zie-fix"
   - All tasks in plan complete → "Ready to release: /zie-release"
   - Always available: "/zie-status | /zie-backlog | /zie-implement | /zie-fix |
     /zie-release | /zie-retro"

## Notes

- Fast — no LLM, no network calls
- Safe to run anytime, even mid-session
