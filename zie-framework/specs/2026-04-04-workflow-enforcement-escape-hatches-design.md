# Workflow Enforcement and Escape Hatches — Design Spec

**Problem:** The SDLC pipeline can be bypassed entirely — users can edit files, push, and deploy without any active workflow track, making compliance dependent on discipline rather than structure.
**Approach:** Extend `intent-sdlc.py` (UserPromptSubmit hook) to detect a "no active track" state when SDLC-adjacent activity is detected, and surface contextual suggestions for the right workflow track (standard, hotfix, spike, or chore). Add a drift log that records bypass events with reason. Update `/zie-status` to show the drift event count. No hard blocks — always offer an alternative.
**Components:**
- `hooks/intent-sdlc.py` — detect no-active-track state and emit track suggestion; calls `utils_roadmap.is_track_active()` to determine active state; owns the prompt output logic
- `hooks/utils_roadmap.py` — provides `is_track_active() -> bool` helper: returns `True` if any Now-lane item exists in `ROADMAP.md` or a drift active-track marker is open in `.drift-log`; no I/O side effects, pure read
- `zie-framework/.drift-log` — append-only NDJSON audit trail of bypass/escape events
- `commands/zie-status.md` — surface drift count in status output
- `commands/zie-hotfix.md` — new lightweight command: describe → fix → ship; signature: `/zie-hotfix [slug] <description>` — `description` is required when no `slug` is provided; slug is auto-derived from description when omitted; differs from `/zie-implement` in that it skips backlog/spec/plan stages, creates a minimal ROADMAP entry tagged `hotfix`, and completes in a single session
- `commands/zie-spike.md` — new lightweight command: sandbox experiment, no ROADMAP entry
- `commands/zie-chore.md` — new lightweight command: maintenance task, no spec required
- `hooks/utils_drift.py` — shared helper: append drift event, read count

**Data Flow:**

1. User sends a prompt that has an SDLC keyword (edit/fix/build/implement etc.)
2. `intent-sdlc.py` runs existing intent detection
3. New check: if intent is `implement` or `fix` AND `utils_roadmap.is_track_active()` returns `False` → emit track-selection prompt (not a block); the prompt fires on every matching prompt in the session until a track becomes active — this is intentional because the hook has no persistent session state, but the suggestion is brief (one line + four options) to minimise alert fatigue; once a track is active the check suppresses it
4. Prompt lists: standard (`/zie-backlog → /zie-spec → /zie-plan → /zie-implement`), hotfix (`/zie-hotfix`), spike (`/zie-spike`), chore (`/zie-chore`)
5. User invokes e.g. `/zie-hotfix <slug>` → command writes an active-track marker to `.drift-log` with `{ts, track, slug, reason}`
6. Once track is active, the same check in step 3 finds the active track and suppresses the suggestion
7. When track completes (command exits cleanly or `/zie-status` is run), the drift event is marked closed
8. `/zie-status` reads drift event count from `.drift-log` and shows `drift: N bypass events` in the status block

**Edge Cases:**
- No active track AND no SDLC keyword → no suggestion emitted (no false positives on general chat)
- Drift log missing or unreadable → silently skip count; no crash
- Concurrent writes to `.drift-log` → append mode is atomic per-line on POSIX; no locking needed for single-user CLI
- `/zie-hotfix` run with no active ROADMAP item → valid; creates a minimal backlog entry tagged `hotfix` in Done after ship
- `/zie-spike` deliberately does NOT write to ROADMAP — output is a local `spike-<slug>/` directory only
- Drift log grows unbounded → trim to last 200 events on write (rolling window)

**Out of Scope:**
- Hard blocks (exit 2) on direct file edits — backlog explicitly excludes this
- Enforcement of drift-log review in CI — audit trail only, no gate
- Auto-escalation from hotfix/chore to full pipeline — too complex for initial scope
- Multi-user / team drift aggregation — solo developer framework
- Chore scope heuristic (line count delta escalation) — noted as future enhancement
