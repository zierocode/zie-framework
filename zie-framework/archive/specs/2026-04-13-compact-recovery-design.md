---
status: approved
approved_by: autonomous-sprint
approved_at: 2026-04-13
clarity: 5
---

# compact-recovery — Design Spec

## Problem

When Claude Code compacts conversation context (automatic or `/compact`), the workflow often stalls or loses track. The current `sdlc-compact.py` hook saves a snapshot to `/tmp` and restores via `additionalContext`, but five specific gaps remain:

1. **Ephemeral `/tmp` snapshots** — snapshots stored in `/tmp` are lost on machine restart; PostCompact falls back to live ROADMAP (no TDD phase, no changed-files list, no git branch).
2. **Multi-level compaction overwrite** — each PreCompact overwrites the single snapshot; no history so a double-compact loses the earlier snapshot entirely.
3. **No active-workflow verification** — PostCompact restores SDLC context but does not check whether a sprint is active; the model may drift to a different task after compact.
4. **Thin sprint state** — `.sprint-state` tracks `phase`, `items`, `remaining_items`, `completed_phases`, `started_at` but not `current_task`, `tdd_phase`, or `last_action`; after a compact mid-Phase 2 item, the model knows *which* items remain but not *what it was doing inside* the current item.
5. **Over-engineered compact-hint tiers** — 3 tiers (70/80/90%) produce noise; most sessions only need a nudge and a hard limit.

## Motivation

Context compaction is the #1 cause of workflow stalls. After a compact, the model "forgets" where it was and either stops working or starts a different task. This is especially painful during long `/implement` sessions and sprint Phase 2 loops.

## Goals

- G1: PostCompact always restores enough context to continue the active workflow without drift.
- G2: `.sprint-state` carries within-item granularity so compact recovery knows the exact resumption point.
- G3: Compact-hint system is simpler with fewer tiers, reducing noise without losing the critical hard-limit signal.

## Non-Goals

- Not restoring tool-call history or file-edit state (impossible via hook output).
- Not preventing compaction itself.
- Not changing Phase 1, 3, or 4 state granularity.
- Not adding new configuration keys beyond the tier-threshold renames.

## Design

### Change 1 — Persistent snapshot storage

**File:** `hooks/sdlc-compact.py`

Current: PreCompact writes snapshot to `project_tmp_path("compact-snapshot", project_name)` which resolves to `/tmp/zie-<project>-compact-snapshot`.

New: PreCompact writes snapshot to **both** the `/tmp` path (fast, session-scoped) and a persistent path via `persistent_project_path("compact-snapshot", project_name)` which resolves to `$CLAUDE_PLUGIN_DATA/<project>/compact-snapshot`. PostCompact reads from `/tmp` first (fast), then falls back to persistent path, then falls back to live ROADMAP.

This means:
- Normal compaction: reads from `/tmp` (fast, same as today).
- After machine restart: `/tmp` is empty, reads from `$CLAUDE_PLUGIN_DATA` (survives restarts).
- After double-compact: persistent path holds the *latest* snapshot (same overwrite semantics as `/tmp`, but now at least one survives a restart).

Exact changes to `sdlc-compact.py`:

**PreCompact handler** — after the existing `safe_write_tmp(snap_path, json.dumps(snapshot))` call, add:
```python
# Also persist to CLAUDE_PLUGIN_DATA (survives restart)
try:
    persist_path = persistent_project_path("compact-snapshot", project_name)
    safe_write_persistent(persist_path, json.dumps(snapshot))
except Exception as e:
    print(f"[zie-framework] sdlc-compact: persistent snapshot write failed: {e}", file=sys.stderr)
```

Import addition at top:
```python
from utils_io import project_tmp_path, safe_write_tmp, persistent_project_path, safe_write_persistent
```

**PostCompact handler** — change snapshot read logic from:
```python
if snap_path.exists():
    snapshot = json.loads(snap_path.read_text())
```
to a 3-tier fallback:
```python
# 1. /tmp (fast, same-session)
# 2. CLAUDE_PLUGIN_DATA (persistent, survives restart)
# 3. live ROADMAP (already exists as fallback)
for path in (snap_path, persistent_project_path("compact-snapshot", project_name)):
    try:
        if path.exists():
            snapshot = json.loads(path.read_text())
            break
    except Exception:
        continue
```

The existing ROADMAP fallback block (when `snapshot is None`) remains unchanged.

### Change 2 — PostCompact active-workflow guard

**File:** `hooks/sdlc-compact.py`

After building the context block in PostCompact, add a check for `.sprint-state`. If it exists, append a mandatory continuation directive to the context block.

Exact addition — after the `context = "\n".join(lines)` line, before `print(json.dumps({"additionalContext": context}))`:

```python
# Active-workflow guard: if sprint is in progress, inject continuation directive
sprint_state_path = zf / ".sprint-state"
if sprint_state_path.exists():
    try:
        sprint_state = json.loads(sprint_state_path.read_text())
        phase = sprint_state.get("phase", "")
        remaining = sprint_state.get("remaining_items", [])
        current_task = sprint_state.get("current_task", "")
        tdd_phase_val = sprint_state.get("tdd_phase", "")
        if phase:
            directive = f"\nSPRINT ACTIVE — Phase {phase}/4 in progress."
            if current_task:
                directive += f" Current task: {current_task}."
            if tdd_phase_val:
                directive += f" TDD phase: {tdd_phase_val}."
            if remaining:
                directive += f" Remaining items: {', '.join(remaining)}."
            directive += " Continue the sprint — do NOT start a new task or switch context."
            lines.append(directive)
            context = "\n".join(lines)
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: sprint-state read failed: {e}", file=sys.stderr)
```

This directive is appended to the same `additionalContext` JSON, so it is injected into the post-compact context window along with the task/branch/file information. The model sees "SPRINT ACTIVE" and the exact resumption point.

### Change 3 — Sprint state enrichment

**File:** `commands/sprint.md`

Extend the `.sprint-state` JSON schema to include three new fields:

| Field | Type | Updated when |
|-------|------|-------------|
| `current_task` | `string` | Before each Phase 2 item implementation starts |
| `tdd_phase` | `string` | After each TDD phase transition (`RED`, `GREEN`, `REFACTOR`) |
| `last_action` | `string` | After each significant step (task start, test pass, commit, compact) |

Schema change in the Phase 1 checkpoint:
```
Write `zie-framework/.sprint-state` → {
  "phase": 2,
  "items": <all_slugs>,
  "completed_phases": [1],
  "remaining_items": <ready_slugs>,
  "started_at": <iso_ts>,
  "current_task": "",
  "tdd_phase": "",
  "last_action": "phase1-complete"
}
```

Phase 2 loop additions:

Before starting item implementation (step 1):
```
Update .sprint-state: current_task = <slug>, tdd_phase = "", last_action = "impl-start"
```

After TDD phase transitions (within the implement agent, noted in the sprint command):
```
Update .sprint-state: tdd_phase = "RED" | "GREEN" | "REFACTOR"
```

After item completes (step 3, existing):
```
Update .sprint-state: remaining_items = remaining_items - [<slug>], current_task = "", last_action = "impl-done:<slug>"
```

After compact between items (step 3, existing):
```
Update .sprint-state: last_action = "compact-after:<slug>"
```

Phase 3 checkpoint:
```
Write .sprint-state: current_task = "release", last_action = "release-start"
```

Phase 4 checkpoint (existing): delete `.sprint-state`.

**Note:** `tdd_phase` updates during implementation happen by the implement command writing to `.sprint-state`. The sprint command documents this; the implement command (run via `make zie-implement`) needs a small addition.

**File:** `commands/implement.md`

Add to the TDD loop step (step 2 in the task loop):
```
After each TDD phase print (RED/GREEN/REFACTOR), write current TDD phase to .sprint-state:
  Update zie-framework/.sprint-state: tdd_phase = "<phase>"
```

This is a best-effort write — if `.sprint-state` does not exist (non-sprint impl), skip silently.

### Change 4 — Compact-hint tier consolidation

**File:** `hooks/compact-hint.py`

Consolidate from 3 tiers (70/80/90%) to 2 tiers (75/90%):

| Old Tier | Old Threshold | New Tier | New Threshold | Behavior |
|----------|--------------|----------|--------------|----------|
| 1 (soft) | 70% | Advisory | 75% | "Context at 75% — consider /compact soon to stay efficient." |
| 2 (mid) | 80% | *removed* | — | — |
| 3 (hard) | 90% | Mandatory | 90% | "Context at 90% — too full for heavy commands. Start a fresh session." (unchanged text) |

Exact changes:

Remove `soft_threshold` and `threshold` variables. Replace with:
```python
advisory_threshold = config.get("compact_advisory_threshold", 0.75)
mandatory_threshold = config.get("compact_mandatory_threshold", 0.90)
```

Remove the `elif pct >= threshold:` branch (80% mid-tier).

Rename tier flag files:
- `compact-tier-70-<sid>` and `compact-tier-80-<sid>` → consolidated to `compact-tier-advisory-<sid>`
- `compact-tier-90-<sid>` → `compact-tier-mandatory-<sid>`

Update `_tier_fired` and `_mark_tier` calls accordingly.

**File:** `hooks/utils_config.py`

Remove old config keys from `CONFIG_SCHEMA`:
- Remove `compact_hint_threshold` (was 0.8 mid-tier)
- Remove `compact_soft_threshold` (was 0.7)

Add new config keys:
```python
"compact_advisory_threshold": (0.75, float),
"compact_mandatory_threshold": (0.90, float),
```

**File:** `tests/unit/test_compact_hint_tiers.py`

Update all tests:
- `TestSoftTier70` → `TestAdvisoryTier75`: test fires at 75%, not at 74%, fires once per session.
- `TestMidTier80` → removed (no mid-tier).
- `TestHardTier90` → `TestMandatoryTier90`: test fires at 90%, unchanged behavior.

**File:** `tests/unit/test_hooks_compact_hint.py`

Update existing tests:
- `test_hint_printed_when_above_threshold`: adjust from 85%/80% boundary to 80%/75% boundary.
- `test_no_hint_when_below_soft_threshold`: adjust from 65% to 70% (below 75% advisory).
- `test_threshold_configurable`: use new config keys `compact_advisory_threshold` and `compact_mandatory_threshold`.

Clean up tier-flag references from `70`/`80`/`90` to `advisory`/`mandatory`.

## Acceptance Criteria

- AC1: `sdlc-compact.py` PreCompact writes snapshot to both `/tmp` and `$CLAUDE_PLUGIN_DATA`; PostCompact reads `/tmp` first, then persistent path, then live ROADMAP.
- AC2: `sdlc-compact.py` PostCompact appends "SPRINT ACTIVE" directive when `.sprint-state` exists and includes `current_task`, `tdd_phase`, and `remaining_items` in the directive.
- AC3: `commands/sprint.md` `.sprint-state` JSON includes `current_task`, `tdd_phase`, and `last_action` fields; these are updated at the documented checkpoints.
- AC4: `commands/implement.md` TDD loop writes `tdd_phase` to `.sprint-state` on each phase transition.
- AC5: `hooks/compact-hint.py` has 2 tiers (advisory 75%, mandatory 90%); no 80% mid-tier.
- AC6: `hooks/utils_config.py` CONFIG_SCHEMA has `compact_advisory_threshold` and `compact_mandatory_threshold`; old `compact_hint_threshold` and `compact_soft_threshold` removed.
- AC7: All existing tests updated for new tier names and thresholds; all pass.
- AC8: No new Python files, no new hook registrations in `hooks.json`.

## Edge Cases

- `$CLAUDE_PLUGIN_DATA` not set: `persistent_project_path()` falls back to `/tmp` with stderr warning (existing behavior from `utils_io.py`); PostCompact still works via `/tmp` or live ROADMAP.
- `.sprint-state` malformed JSON: PostCompact active-workflow guard catches `Exception`, logs to stderr, continues without directive.
- `.sprint-state` absent (non-sprint session): guard is a no-op; PostCompact context block is same as today.
- Implement command running outside sprint (`.sprint-state` absent): TDD phase write is skipped silently.
- Concurrent PreCompact writes: `safe_write_persistent()` uses `os.replace()` (atomic); PostCompact reads either the previous or new snapshot — both valid.

## Out of Scope

- Snapshots with versioning/history (only latest is kept).
- Auto-triggering `/compact` (user or sprint command must trigger).
- Restoring tool-call history or file-edit state.
- Changing SubagentStart or other hook events.