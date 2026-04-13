---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
---

# compact-recovery — Implementation Plan

## Summary

4 changes: persistent snapshot, PostCompact sprint guard, enriched sprint state, 2-tier compact hints.

## Task 1 — Persistent snapshot in sdlc-compact.py

**Goal:** PreCompact writes to both `/tmp` and `$CLAUDE_PLUGIN_DATA`; PostCompact reads `/tmp` then persistent then live ROADMAP.

### Steps

1. **Edit `hooks/sdlc-compact.py`** — update import line:
   - Change: `from utils_io import project_tmp_path, safe_write_tmp`
   - To: `from utils_io import project_tmp_path, safe_write_tmp, persistent_project_path, safe_write_persistent`

2. **Edit `hooks/sdlc-compact.py`** — PreCompact handler, after `safe_write_tmp(snap_path, json.dumps(snapshot))`:
   - Add persistent write block:
   ```python
   try:
       persist_path = persistent_project_path("compact-snapshot", project_name)
       safe_write_persistent(persist_path, json.dumps(snapshot))
   except Exception as e:
       print(f"[zie-framework] sdlc-compact: persistent snapshot write failed: {e}", file=sys.stderr)
   ```

3. **Edit `hooks/sdlc-compact.py`** — PostCompact handler, replace single snapshot read with 3-tier fallback:
   - Replace:
   ```python
   if snap_path.exists():
       snapshot = json.loads(snap_path.read_text())
   ```
   - With:
   ```python
   for _read_path in (snap_path, persistent_project_path("compact-snapshot", project_name)):
       try:
           if _read_path.exists():
               snapshot = json.loads(_read_path.read_text())
               break
       except Exception:
           continue
   ```

4. **Write `tests/unit/test_sdlc_compact_persistent.py`** — new test file:
   - `test_precompact_writes_persistent`: mock `CLAUDE_PLUGIN_DATA`, verify file created under persistent dir.
   - `test_postcompact_reads_persistent_fallback`: delete `/tmp` snapshot after PreCompact, verify PostCompact reads from persistent path.
   - `test_postcompact_roadmap_fallback_when_both_missing`: delete both `/tmp` and persistent snapshots, verify PostCompact falls back to ROADMAP.
   - `test_persistent_write_failure_does_not_block`: mock `safe_write_persistent` to raise, verify PreCompact still writes `/tmp` and exits 0.

## Task 2 — PostCompact active-workflow guard

**Goal:** When `.sprint-state` exists, PostCompact appends "SPRINT ACTIVE" directive.

### Steps

1. **Edit `hooks/sdlc-compact.py`** — PostCompact handler, after `context = "\n".join(lines)` and before `print(json.dumps({"additionalContext": context}))`:
   - Add sprint-state guard block (reads `zf / ".sprint-state"`, parses JSON, appends directive with `phase`, `current_task`, `tdd_phase`, `remaining_items`).
   - Guard catches all exceptions, logs to stderr, continues.

2. **Write `tests/unit/test_sdlc_compact_sprint_guard.py`** — new test file:
   - `test_sprint_guard_injected_when_state_exists`: create `.sprint-state` with `phase=2, remaining_items=["item-b"], current_task="item-a"`, verify `additionalContext` contains "SPRINT ACTIVE" and task details.
   - `test_sprint_guard_skipped_when_no_state`: no `.sprint-state` file, verify no "SPRINT ACTIVE" in output.
   - `test_sprint_guard_handles_malformed_state`: write invalid JSON to `.sprint-state`, verify hook exits 0 and logs error.
   - `test_sprint_guard_includes_tdd_phase`: `.sprint-state` has `tdd_phase="GREEN"`, verify directive mentions "TDD phase: GREEN".

## Task 3 — Sprint state enrichment

**Goal:** `.sprint-state` includes `current_task`, `tdd_phase`, `last_action`; updated at documented checkpoints.

### Steps

1. **Edit `commands/sprint.md`** — Phase 1 checkpoint (after "Write `zie-framework/.sprint-state`"):
   - Add `current_task`, `tdd_phase`, `last_action` fields to JSON.

2. **Edit `commands/sprint.md`** — Phase 2 loop, step 1 (move item to Now):
   - Add: "Update `.sprint-state`: `current_task = <slug>`, `tdd_phase = ""`, `last_action = "impl-start"`"

3. **Edit `commands/sprint.md`** — Phase 2 loop, step 3 (after item success):
   - Update existing `remaining_items` line to also set: `current_task = ""`, `last_action = "impl-done:<slug>"`

4. **Edit `commands/sprint.md`** — Phase 2 loop, compact step (between items):
   - Add: "Update `.sprint-state`: `last_action = "compact-after:<slug>"`"

5. **Edit `commands/sprint.md`** — Phase 3 checkpoint:
   - Add: `current_task = "release"`, `last_action = "release-start"`

6. **Edit `commands/implement.md`** — Task loop step 2 (TDD loop):
   - Add after each TDD phase print: "Write current TDD phase to `zie-framework/.sprint-state`: update `tdd_phase` field (skip silently if file absent)."

7. **Update `tests/unit/test_sprint_state.py`**:
   - Add test: `"current_task"` key appears in sprint.md `.sprint-state` JSON examples.
   - Add test: `"tdd_phase"` key appears in sprint.md `.sprint-state` JSON examples.
   - Add test: `"last_action"` key appears in sprint.md `.sprint-state` JSON examples.
   - Add test: `implement.md` references `.sprint-state` for `tdd_phase` writes.

## Task 4 — 2-tier compact hints

**Goal:** Consolidate from 3 tiers (70/80/90%) to 2 tiers (advisory 75%, mandatory 90%).

### Steps

1. **Edit `hooks/compact-hint.py`**:
   - Replace `soft_threshold`, `threshold`, `hard_threshold` with `advisory_threshold` and `mandatory_threshold`.
   - Read from config: `compact_advisory_threshold` (default 0.75), `compact_mandatory_threshold` (default 0.90).
   - Remove the 80% mid-tier branch.
   - Rename tier flags from `compact-tier-70/80/90-<sid>` to `compact-tier-advisory-<sid>` and `compact-tier-mandatory-<sid>`.
   - Update advisory message: `"[zie-framework] Context at {pct_int}% — consider /compact soon to stay efficient."`
   - Mandatory message: unchanged from current 90% hard warning.

2. **Edit `hooks/utils_config.py`**:
   - Remove `compact_hint_threshold` from `CONFIG_SCHEMA`.
   - Add `compact_advisory_threshold: (0.75, float)` and `compact_mandatory_threshold: (0.90, float)` to `CONFIG_SCHEMA`.

3. **Edit `tests/unit/test_compact_hint_tiers.py`**:
   - Rename `TestSoftTier70` to `TestAdvisoryTier75`; update threshold values (75% instead of 70%).
   - Remove `TestMidTier80` class entirely.
   - Rename `TestHardTier90` to `TestMandatoryTier90`; update flag name references.
   - Update `_flag()` helper and `_clean()` methods to use `advisory`/`mandatory` instead of `70`/`80`/`90`.

4. **Edit `tests/unit/test_hooks_compact_hint.py`**:
   - Update `TestHintPrinted`: change 85%/80% test to 80%/75% boundary.
   - Update `TestNoHint`: change below-threshold test from 65% to 70%.
   - Update `TestThresholdConfig`: use `compact_advisory_threshold` and `compact_mandatory_threshold`.
   - Update `_clean_tier_flags()` to use `advisory`/`mandatory` instead of `70`/`80`/`90`.

5. **Run `make test-unit`** to verify all tests pass.

## Dependency Order

```
Task 4 (compact-hint tiers) → independent, can go first or last
Task 1 (persistent snapshot) → must come before Task 2 (sprint guard reads persistent path)
Task 2 (sprint guard) → depends on Task 1
Task 3 (sprint state enrichment) → independent of Tasks 1/2; sprint guard (Task 2) reads the new fields, but works without them
```

Recommended order: Task 4, Task 1, Task 2, Task 3.

## Verification

After all tasks:
1. `make test-unit` passes.
2. `make lint` passes.
3. Manual: trigger `/compact` during sprint Phase 2, verify PostCompact context includes "SPRINT ACTIVE" directive with task details.
4. Manual: restart machine, start new Claude session, verify PostCompact reads persistent snapshot.