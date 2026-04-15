---
description: Show current SDLC state — active feature, ROADMAP summary, test health, and next suggested command.
allowed-tools: Read, Bash, Glob
model: haiku
effort: low
---

# /status — Show current SDLC state

<!-- preflight: minimal -->

Concise snapshot of project state. No LLM reasoning — just read files and print.

**Live context (injected at load):**

ROADMAP snapshot (first 30 lines):
!`cat zie-framework/ROADMAP.md | head -30`

Knowledge hash (bind as `current_hash_injected`):
!`python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"`

## Steps

1. **Check initialization** — `zie-framework/` absent → "Not initialized. Run /init first." Stop.
2. **Read files** — `.config` (incl. `knowledge_hash`, `knowledge_synced_at`), `VERSION`, specs/plans dirs. Read drift count from `.drift-log` (non-empty lines; 0 if missing). Tail last 5 non-empty lines from failure-log (clip at 120 chars). For ROADMAP: targeted reads only — Grep `## Now` → read to next `---`; count `- [` in Next/Done (count only, no content).
3. **Find active plan** — most recent file in `plans/` where ROADMAP Now is not empty.
4. **Knowledge drift** — compare `current_hash_injected` to stored `knowledge_hash`:

   | Comparison | Status |
   | --- | --- |
   | Missing hash | `? no baseline — run /resync` |
   | Equal | `✓ synced (<knowledge_synced_at>)` |
   | Differs | `⚠ drift detected — run /resync` |

5. **Test health** — detect runner from `.config`:

   | Runner | Cache check | Result |
   | --- | --- | --- |
   | pytest | `.pytest_cache/v/cache/lastfailed` | Non-empty → ✗, Empty → ✓, No dir → ? |
   | pytest | `.pytest_cache/` mtime vs `tests/` mtime | Newer test file → ? stale (overrides above) |
   | vitest/jest | Cache dir timestamp | No cache → ? stale |

6. **Release velocity** — single Bash call:
   ```bash
   git log --tags --simplify-by-decoration --pretty="%D|%ai" | grep -E 'tag: v?[0-9]+\.[0-9]+\.[0-9]+' | head -6
   ```
   Parse semver tag + date per line. Compute intervals between consecutive pairs.
   Fewer than 2 entries → "Velocity: not enough releases yet". Otherwise → `"Velocity (last N): Xd, Yd, …"`

7. **Print status**:

   ```
   ## สถานะ <project>

   project: <dir>(<type>) v<VERSION> | brain: <on|off> | drift: <N>
   knowledge: <✓ synced | ⚠ drift | ? no baseline>
   velocity: <velocity string>

   **ROADMAP**
   - now: <N> in progress | next: <N> queued | done: <N> shipped

   **งานปัจจุบัน**: <first Now item or "ยังไม่มีงาน">
   **Plan**: <plans/latest.md or "ยังไม่มี plan">

   tests: unit:<✓|✗|?|n/a> int:<✓|✗|?|n/a> e2e:<✓|✗|?|n/a>

   **ขั้นตอนถัดไป**: <context-appropriate suggestion>

   config: safety=<mode> mem=<on|off> pw=<on|off> drift=<N>

   failures:
   <tail last 5 from failure-log, each clipped at 120 chars>
   ```

7.5 **Pipeline stage** — per Now item, detect backlog→spec→plan→implement→release→retro completion. Print: `Pipeline: backlog ✓ → spec ✓ → plan ✓ → implement ▶ → release — → retro —`. Skip if Now is empty.

7.6 **Pipeline detail** — per Now+Ready slug: read backlog `## Problem` excerpt (truncated to 120 chars), check spec/plan status. Print: `- <slug>: <excerpt> | spec <✓|—> plan <✓|—>`. Skip if both lanes empty.

8. **Next step logic**:

   | Condition | Suggestion |
   | --- | --- |
   | Nothing in Now | "Start a feature: /backlog" |
   | Active plan, tasks incomplete | "Continue: /implement" |
   | Tests stale or failing | "Fix tests: /fix" |
   | All tasks complete | "Ready to release: /release" |

   Always show: `/status | /backlog | /implement | /fix | /release | /retro | /sprint`

→ /next for recommended backlog items