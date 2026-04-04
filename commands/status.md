---
description: Show current SDLC state — active feature, ROADMAP summary, test health, and next suggested command.
allowed-tools: Read, Bash, Glob
model: haiku
effort: low
---

# /status — Show current SDLC state

Show a concise snapshot of where the project is right now. No LLM reasoning
needed — just read files and print.

## Steps

**Live context (injected at command load):**

ROADMAP snapshot (first 30 lines):
!`cat zie-framework/ROADMAP.md | head -30`

Knowledge hash:
!`python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"`

1. **Check initialization**: if `zie-framework/` does not exist → print "Not
   initialized. Run /init first." and stop.

2. **Read files**: `zie-framework/.config` (including `knowledge_hash`,
   `knowledge_synced_at`), `VERSION`, specs/plans dirs เพื่อ context.
   Read drift count from `zie-framework/.drift-log` — count non-empty lines
   (each line is one drift event). If file missing → count is 0.
   For ROADMAP.md — use targeted reads only:
   - **Now section**: Grep `## Now` → Read from that line to next `---` separator.
   - **Next count**: Grep `- [` lines between `## Next` and next `---` → count only.
   - **Done count**: Grep `- [` lines between `## Done` and next `---` → count only.
   Do not load full Next or Done section content.

3. **Find active plan**: most recent file in `zie-framework/plans/` where
   ROADMAP.md "Now" section is not empty.

4. **Check knowledge drift** via Bash — must use the **same algorithm**
   as `/resync` and `/init`:

   ```bash
   python3 hooks/knowledge-hash.py
   ```

   - Read `knowledge_hash` from `zie-framework/.config`
   - If missing → Knowledge status: `? no baseline — run /resync`
   - Compare script output to stored hash:
     - Equal → `✓ synced (<knowledge_synced_at>)`
     - Differs → `⚠ drift detected — run /resync`
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

6. **Compute release velocity** via a single Bash call:

   ```bash
   git log --tags --simplify-by-decoration --pretty="%D|%ai" | \
     grep -E 'tag: v?[0-9]+\.[0-9]+\.[0-9]+' | head -6
   ```

   Each output line contains ref decorations and ISO author-date separated by `|`.
   Parse the first semver tag (`v?X.Y.Z`) and the date (`YYYY-MM-DD`) from each line.

   - Collect up to 6 entries (to compute up to 5 intervals).
   - For each consecutive pair, compute `days = (date[n] - date[n+1]).days`.
   - Fewer than 2 entries → velocity string = `"Velocity: not enough releases yet"`.
   - Otherwise → `"Velocity (last N): Xd, Yd, Zd, …"` where N = number of intervals (≤ 5).

7. **พิมพ์สถานะ** โดยใช้ markdown format:

   ## สถานะ zie-framework

   | | |
   | --- | --- |
   | โปรเจกต์ | \<directory name> (\<project_type>) |
   | Version | \<VERSION> |
   | Velocity | \<velocity string> |
   | Brain | \<enabled\|disabled> |
   | Drift | \<N> bypass events (`zie-framework/.drift-log`) |
   | Knowledge | \<✓ synced (date) \| ⚠ drift: /resync \| ? no baseline> |

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

7.5 **Pipeline Stage Indicator** — detect active feature's pipeline stage:

   For each item in ROADMAP Now lane, detect which stages are complete:
   - **backlog** ✓ — `zie-framework/backlog/<slug>.md` exists
   - **spec** ✓ — `zie-framework/specs/*-<slug>-design.md` exists with `approved: true`
   - **plan** ✓ — `zie-framework/plans/*-<slug>.md` exists with `approved: true`
   - **implement** ▶ — Now lane has `[ ]` item (in progress)
   - **implement** ✓ — Now lane has `[x]` item (complete, pending release)
   - **release** ✓ — git tag matching current VERSION exists
   - **retro** ✓ — `zie-framework/decisions/` has ADRs dated today

   Print pipeline row:
   ```
   Pipeline: backlog ✓ → spec ✓ → plan ✓ → implement ▶ → release — → retro —
   ```
   If Now lane is empty: skip pipeline row.

8. **ตรรกะขั้นตอนถัดไป** (เลือกที่เกี่ยวข้องที่สุด):
   - Nothing in ROADMAP Now → "Start a feature: /backlog"
   - Active plan exists, tasks incomplete → "Continue: /implement"
   - Tests stale or failing → "Fix tests: /fix"
   - All tasks in plan complete → "Ready to release: /release"
   - Always available: "/status | /backlog | /implement | /fix |
     /release | /retro | /sprint"

## Notes

- Fast — no LLM, no network calls
- Safe to run anytime, even mid-session
