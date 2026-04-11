---
approved: true
approved_at: 2026-04-11
backlog:
---

# Intent Intelligence — Design Spec

**Problem:** Claude responds to instructions literally but doesn't detect deeper intent. "ทำเลย" skips the pipeline; short ambiguous messages get answered without clarification; sprint intent completes without verifying spec/plan exist. The framework has no structured intent layer.

**Approach:** Two components — (A) extend existing `intent-sdlc.py` UserPromptSubmit hook with threshold-based scoring for sprint/fix/chore/unclear intents; (B) new `stop-pipeline-guard.py` Stop hook: verify that sprint-intent sessions produced approved spec + plan artifacts.

**Note on brainstorm signals:** The brainstorm intent pattern group is defined in the brainstorming-skill spec and implemented in `intent-sdlc.py`. This spec handles sprint/fix/chore/unclear intents only.

**Relationship to intent-sdlc.py:** `intent-sdlc.py` already has sprint/fix/chore patterns. This spec's intent scoring is implemented by **extending `intent-sdlc.py`** (not a new hook file) to add the threshold-based scorer, JSON additionalContext output, and the sprint-flag write. There is no `intent-classify.py` file — all logic lives in the existing hook to prevent double-firing. `hooks.json` requires no change.

**Out of Scope:** Intent history not persisted across sessions. Signal weights are static (no adaptive learning — covered by adaptive-learning spec). No mid-session intent change handling. Single-session scope only.

**Components:**
- `hooks/intent-sdlc.py` — extend with threshold-based scoring for sprint/fix/chore/unclear + sprint-flag write (no new hook file)
- `hooks/stop-pipeline-guard.py` — new Stop hook; checks for sprint-intent flag → warns if no approved artifacts
- `hooks/hooks.json` — add stop-pipeline-guard.py to Stop array only (intent-sdlc.py already registered)
- Session flag: `project_tmp_path("intent-sprint-flag", project)` — written by intent-sdlc.py, read by stop-pipeline-guard.py

**Session State (using `project_tmp_path()` from `utils_io.py`):**
- `project_tmp_path("intent-sprint-flag", project)` — flag file; written when sprint intent detected, read by Stop hook
- Format: plain text flag file (existence check only)
- Cleanup: `session-cleanup.py` glob-deletes all `zie-<project>-*` tmp files automatically — no change to session-cleanup.py required. `stop-pipeline-guard.py` already deletes the flag in step 5; session-cleanup.py is a safety net for interrupted sessions only.

**Data Flow:**

*A — intent-sdlc.py extension (UserPromptSubmit, synchronous):*

Intent signal table (threshold ≥ 2 matching signals):

| Intent | Signals | Hint injected |
|--------|---------|---------------|
| `sprint` | ทำเลย, implement, build, สร้าง, เพิ่ม feature, start coding | confirm backlog→spec→plan before implementing |
| `fix` | bug, broken, error, ไม่ work, crash, fail, แก้ | invoke fix/debug track |
| `chore` | update, bump, rename, cleanup, refactor, ลบ | use /chore to track |
| `unclear` | message length < 15 chars AND no signal from any other intent matches | ask clarifying question first |

`unclear` heuristic: length-based only (< 15 chars) combined with zero SDLC keyword matches — no verb/subject NLP required. Consistent with existing `intent-sdlc.py` `len(message) < 15` early-exit pattern.

Scoring: count matching signals per intent → top score ≥ threshold → inject hint
If no intent clears threshold → exit 0 silently (no hint)

**Threshold scope:** The ≥ 2 threshold applies only to the four new intents (sprint/fix/chore/unclear). All other existing intents in `intent-sdlc.py` retain the current `>= 1` threshold unchanged.

**`unclear` path:** The existing `len(message) < 15` silent early-exit in `intent-sdlc.py` is **removed** and replaced by the `unclear` hint path. Short messages (< 15 chars with no SDLC keyword matches) now inject the clarifying question hint instead of silently exiting.

**`stop-pipeline-guard.py` async:** Synchronous (no `"background": true` flag in hooks.json). Must complete and emit its warning before the session closes — consistent with `stop-guard.py` pattern.

When sprint intent detected: also write `project_tmp_path("intent-sprint-flag", project)` flag

Hint format (UserPromptSubmit hooks output JSON `additionalContext`, not plain text):
```json
{"additionalContext": "[zie-framework] intent: <type> — <guidance>"}
```

*B — stop-pipeline-guard.py (Stop hook):*
1. Check `project_tmp_path("intent-sprint-flag", project)` — if not exists: exit 0 (no sprint intent this session)
2. Scan `zie-framework/specs/` for files modified today containing `approved: true`
3. Scan `zie-framework/plans/` for files modified today containing `approved: true`
4. If neither found → print warning:
   ```
   [zie-framework] sprint intent detected but no approved spec/plan found this session
   ```
5. Delete `project_tmp_path("intent-sprint-flag", project)` flag (cleanup)
6. Warning only — never block. Always exit 0.

**Error Handling:**
- intent-sdlc.py extension: inherits existing Tier 1 outer guard (bare except → exit 0), never blocks Claude
- Malformed event / missing message field: exit 0 silently
- Flag write failure: log warning, continue (guard may not fire — acceptable)
- stop-pipeline-guard.py: Tier 1 outer guard (bare except → exit 0)
- Flag unreadable: exit 0 silently (skip guard)
- zie-framework/ dir absent: exit 0 (not a zie-framework project, guard not applicable)

**Testing:**
- `tests/unit/test_intent_sdlc_sprint.py` (extend existing file — sprint/flag cases already live here):
  - Unit: sprint signals score correctly in Thai + English
  - Unit: sprint intent writes flag file
  - Unit: fix signals trigger fix hint
  - Unit: short ambiguous message (< 15 chars, no SDLC keywords) triggers unclear hint
  - Unit: clear non-matching message → no hint, exit 0 silently
  - Unit: exits 0 on malformed event (@pytest.mark.error_path)
- `tests/unit/test_stop_pipeline_guard.py` (new file):
  - Unit: guard warns when sprint flag present + no approved artifacts
  - Unit: guard silent when sprint flag present + approved artifacts exist
  - Unit: guard exits 0 when sprint flag absent
  - Unit: guard exits 0 when zie-framework/ absent
  - Unit: guard exits 0 on malformed event (@pytest.mark.error_path)
