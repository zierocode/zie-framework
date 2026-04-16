---
description: Show current SDLC state — active feature, ROADMAP, test health, and next suggested command. Supports --guide, --health, and --brief flags.
argument-hint: "[--guide|--health|--brief]"
allowed-tools: Read, Bash, Glob, Grep
model: haiku
effort: low
---

# /status — Show current SDLC state

<!-- preflight: minimal -->

Concise snapshot of project state. No LLM reasoning — just read files and print.

Supports three flags for expanded views:
- `--guide`: Show framework command map and recommended next actions (merged from /guide)
- `--health`: Show hook health, session state, and config validation (merged from /health)
- `--brief`: Show the active design brief from .zie/handoff.md (merged from /brief)

**Live context (injected at load):**

ROADMAP snapshot (first 30 lines):
!`cat zie-framework/ROADMAP.md | head -30`

Knowledge hash (bind as `current_hash_injected`):
!`python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"`

## Steps

1. **Parse flags** — check `$ARGUMENTS` for `--guide`, `--health`, `--brief`.

### If --brief

2. Check `$CWD/.zie/handoff.md`:
   - If absent → print "No active design brief — run a design conversation first, or invoke zie-framework:brainstorm to start a structured session."
   - If present → display full content formatted, then print:
     ```
     Brief captured at: <captured_at value>
     Source: <source value>

     Run /sprint <feature-name> to start the pipeline with this brief.
     Run /sprint without arguments to be prompted for a topic.
     ```
   Stop.

### If --health

2. **Validate hooks.json config**
   - Read `hooks/hooks.json` — verify valid JSON
   - For each hook command entry: check that the referenced `.py` file exists on disk
   - Record: `[✅]` if found, `[❌ missing]` if not

3. **Check recent hook activity**
   - Scan `/tmp/zie-<project>-*` flags for timestamps using `ls -la`
   - Map flag names to hook names:
     - `session-context-*` → subagent-context (active session)
     - `last-test` → auto-test (last test run)
     - `intent-sprint-flag` → intent-sdlc (sprint detected)
     - `design-mode` → intent-sdlc (design conversation active)
   - Compute age of each flag

4. **Read session state**
   - Check `zie-framework/.config` — show enabled features (zie_memory, playwright)
   - Check if roadmap cache is fresh

5. **Print health report**

   ```
   zie-framework health — <project>

   Config
     [✅] hooks.json valid JSON
     [✅] All hook scripts found on disk

   Hook Activity (this session)
     [✅] intent-sdlc        last signal: 3m ago
     [✅] subagent-context   session cache: active
     [✅] auto-test          last run: 12m ago
     [⬜] intent-sdlc (design)  no activity this session

   Session State
     Branch:   dev
     Features: zie_memory=disabled, playwright=disabled
     Roadmap:  cache fresh (hit 2m ago)

   Pipeline
     Active: <slug or "none">
     ROADMAP: <Now lane summary>
   ```

6. **Config warnings**
   - Missing hook script on disk → `[❌] <hook>.py — script not found at <path>`
   - Invalid JSON in hooks.json → `[❌] hooks.json — JSON parse error`
   - Show each warning clearly but continue report
   - `/tmp` unreadable: skip hook activity section, show "unavailable"
   - Config file missing: show defaults assumed
   - Git command fails: skip branch info

   Stop.

### If --guide

2. **Read current state**
   - Read `zie-framework/ROADMAP.md` (if present):
     - Now lane items → active feature
     - Next lane items → pending work
   - Scan `zie-framework/specs/` for files matching `*-<item-slug>-design.md`:
     - Read YAML frontmatter — check `approved: true`
   - Scan `zie-framework/plans/` for files matching `*-<item-slug>.md`:
     - Read YAML frontmatter — check `approved: true`

3. **Show command overview**

   ```
   ## zie-framework Commands

   | Command | Purpose |
   |---------|---------|
   | /backlog | Capture a new idea |
   | /spec | Design a backlog item |
   | /plan | Plan implementation from approved spec |
   | /implement | TDD implementation |
   | /sprint | Full pipeline in one go |
   | /fix | Debug and fix (use --hotfix for emergencies) |
   | /status | Show current SDLC state |
   | /next | Recommended backlog items |
   | /audit | Project audit |
   | /retro | Post-release retrospective |
   | /release | Merge dev→main, version bump |
   | /resync | Refresh project knowledge |
   | /init | Bootstrap zie-framework |

   Workflow: backlog → spec (reviewer) → plan (reviewer) → implement → release → retro
   Use /sprint to run the full pipeline in one session.
   ```

4. **Determine pipeline position and recommend next actions**

   For each Next-lane item:
   - No spec → `/spec <item>`
   - Spec not approved → `Skill('zie-framework:spec-review')` then `python3 hooks/approve.py <spec-path>`
   - No plan → `/plan <item>`
   - Plan approved → `/implement` or `/sprint <item>`

   Print recommended next 1-3 actions with exact commands.

   Stop.

### Default (no flag) — status report

2. **Check initialization** — `zie-framework/` absent → "Not initialized. Run /init first." Stop.
3. **Read files** — `.config` (incl. `knowledge_hash`, `knowledge_synced_at`), `VERSION`, specs/plans dirs. Read drift count from `.drift-log` (non-empty lines; 0 if missing). Tail last 5 non-empty lines from failure-log (clip at 120 chars). For ROADMAP: targeted reads only — Grep `## Now` → read to next `---`; count `- [` in Next/Done (count only, no content).
4. **Find active plan** — most recent file in `plans/` where ROADMAP Now is not empty.
5. **Knowledge drift** — compare `current_hash_injected` to stored `knowledge_hash`:

   | Comparison | Status |
   | --- | --- |
   | Missing hash | `? no baseline — run /resync` |
   | Equal | `✓ synced (<knowledge_synced_at>)` |
   | Differs | `⚠ drift detected — run /resync` |

6. **Test health** — detect runner from `.config`:

   | Runner | Cache check | Result |
   | --- | --- | --- |
   | pytest | `.pytest_cache/v/cache/lastfailed` | Non-empty → ✗, Empty → ✓, No dir → ? |
   | pytest | `.pytest_cache/` mtime vs `tests/` mtime | Newer test file → ? stale (overrides above) |
   | vitest/jest | Cache dir timestamp | No cache → ? stale |

7. **Release velocity** — single Bash call:
   ```bash
   git log --tags --simplify-by-decoration --pretty="%D|%ai" | grep -E 'tag: v?[0-9]+\.[0-9]+\.[0-9]+' | head -6
   ```
   Parse semver tag + date per line. Compute intervals between consecutive pairs.
   Fewer than 2 entries → "Velocity: not enough releases yet". Otherwise → `"Velocity (last N): Xd, Yd, …"`

8. **Print status**:

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

8.5 **Pipeline stage** — per Now item, detect backlog→spec→plan→implement→release→retro completion. Print: `Pipeline: backlog ✓ → spec ✓ → plan ✓ → implement ▶ → release — → retro —`. Skip if Now is empty.

8.6 **Pipeline detail** — per Now+Ready slug: read backlog `## Problem` excerpt (truncated to 120 chars), check spec/plan status. Print: `- <slug>: <excerpt> | spec <✓|—> plan <✓|—>`. Skip if both lanes empty.

9. **Design brief** — if `.zie/handoff.md` exists, append:
   ```
   **Design brief**: active (captured <captured_at>) → /status --brief to view
   ```

10. **Next step logic**:

    | Condition | Suggestion |
    | --- | --- |
    | Nothing in Now | "Start a feature: /backlog" |
    | Active plan, tasks incomplete | "Continue: /implement" |
    | Tests stale or failing | "Fix tests: /fix" |
    | All tasks complete | "Ready to release: /release" |

    Always show: `/status | /backlog | /implement | /fix | /release | /retro | /sprint`
    Also show: `/status --guide | /status --health | /next`