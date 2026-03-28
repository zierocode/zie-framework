# Architecture: Cleanup and Structural Improvements

**Source**: audit-2026-03-24b M3+M8 + L1-L8 (Agent E)
**Effort**: M
**Score impact**: +6 Medium + +8 Low = +14 (Architecture → 92+)

## Problem

8 architectural issues found — all Low-to-Medium individually, high ROI together:

### 1. Hot-path subprocess calls without caching (M3)
6 hooks call git subprocess on every PostToolUse/Edit event (failure-context,
sdlc-compact, stop-guard, task-completed-gate). No deduplication within a session
window. `sdlc-context.py` has a 300s staleness threshold — similar pattern could
cache git status for 5s.

### 2. High PreToolUse dispatch volume (M8)
PreToolUse runs 2 hooks on every Bash/Write/Edit call: safety-check.py (fast)
+ safety_check_agent.py (spawns claude subprocess). Default config triggers agent
on every command. Should default to "regex" mode with clear docs on "agent" mode.

### 3. Inconsistent ROADMAP parsing error handling (L1)
`parse_roadmap_now()` called in 7 hooks — each handles exceptions differently
(empty list, "unknown", exit 0). `utils.parse_roadmap_now()` should return a
typed default tuple on exception instead of callers each deciding.

### 4. Hardcoded SDLC stage keywords in two places (L2)
`intent-detect.py` PATTERNS dict and `sdlc-context.py` STAGE_KEYWORDS serve
overlapping purposes. Extract shared SDLC_STAGES taxonomy to utils.py.

### 5. ROADMAP Now section assumed to exist (L5)
When ROADMAP.md exists but `## Now` section is missing, all 7 callers silently
get `now_items=[]`. Add optional stderr warning to `parse_roadmap_now()` when
file exists but section is empty/malformed.

### 6. Test indicator patterns hardcoded (L6)
`task-completed-gate.py:24` hardcodes `TEST_INDICATORS = ("test_", "_test.", ...)`
Should be configurable via `.config` for projects with non-standard conventions.

### 7. Hook event schema registry absent (L7)
hooks.json comment block documents output protocol but no formal schema. Add
`hooks/hook-events.schema.json` for event input validation in outer guards.

### 8. Async hook candidates not marked (L8)
Only `subagent-stop.py` is async. Side-effect-only hooks that could safely be
async: `session-learn.py`, `session-cleanup.py`, `notification-log.py`.
Profile and mark appropriate hooks async to reduce session end latency.

## Scope

- `hooks/utils.py`: add git status result caching (5s TTL via /tmp)
- Change safety_check_agent.py default mode config documentation to "regex"
- `hooks/utils.py:parse_roadmap_now()`: standardize return type + add
  `warn_on_empty=False` parameter
- `hooks/utils.py`: add `SDLC_STAGES` shared taxonomy
- `hooks/utils.py:parse_roadmap_now()`: add stderr warn when section missing
- `hooks/task-completed-gate.py`: read TEST_INDICATORS from `.config`
- Create `hooks/hook-events.schema.json`
- Profile Stop/Notification hooks for async candidacy

## Acceptance Criteria

- [ ] Git status cached per session window (configurable TTL)
- [ ] safety_check_agent.py mode defaults documented + "regex" is the safe default
- [ ] parse_roadmap_now() returns consistent typed default on exception
- [ ] SDLC_STAGES in utils.py used by both intent-detect and sdlc-context
- [ ] parse_roadmap_now() warns on empty Now section
- [ ] TEST_INDICATORS configurable via .config
- [ ] hook-events.schema.json created and referenced in hooks.json comments
- [ ] At least 2 additional side-effect hooks marked async
