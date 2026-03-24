---
approved: true
approved_at: 2026-03-24
backlog: backlog/architecture-cleanup.md
---

# Architecture: Cleanup and Structural Improvements — Design Spec

**Problem:** Five lower-priority architectural gaps identified in audit: (1) SDLC stage taxonomy duplicated in two hooks with overlapping but inconsistent structures; (2) `TEST_INDICATORS` hardcoded in `task-completed-gate.py`, blocking projects with non-standard test conventions; (3) `parse_roadmap_now()` provides no signal when the Now section is absent vs present-but-empty; (4) `session-learn.py` and `session-cleanup.py` run synchronously on Stop though they have no return value Claude waits on; (5) no formal schema for hook event inputs.

**Approach:** Five targeted changes, all small: (1) Add `SDLC_STAGES` list to utils.py as shared canonical stage names; (2) Make `TEST_INDICATORS` configurable via `.config`; (3) Add `warn_on_empty=False` parameter to `parse_roadmap_now()`; (4) Add `"async": true` to session-learn and session-cleanup in hooks.json; (5) Create `hooks/hook-events.schema.json`. Git status caching and safety_check_agent mode are intentionally out of scope (see below).

**Components:**

- `hooks/utils.py`
  - Add `SDLC_STAGES: list[str]` — canonical ordered list of SDLC stage names
  - Add `warn_on_empty` parameter to `parse_roadmap_now()`

- `hooks/intent-detect.py`
  - Update `PATTERNS` keys to use `SDLC_STAGES` for stage name validation (import from utils)
  - No pattern changes — just import the stage names

- `hooks/sdlc-context.py`
  - Update `STAGE_KEYWORDS` keys to use `SDLC_STAGES`
  - No keyword changes

- `hooks/task-completed-gate.py`
  - Line 24: make `TEST_INDICATORS` configurable via `.config` key `test_indicators` (comma-separated)
  - Fall back to current hardcoded tuple when key absent

- `hooks/hooks.json`
  - Add `"async": true` to session-learn entry (Stop event)
  - Add `"async": true` to session-cleanup entry (Stop event)

- `hooks/hook-events.schema.json` (new file)
  - JSON Schema for the common hook event envelope

**Data Flow:**

**1. SDLC_STAGES in utils.py:**
```python
# hooks/utils.py
SDLC_STAGES = ["init", "backlog", "spec", "plan", "implement", "fix", "release", "retro"]
```

Usage in `intent-detect.py` — validate stage name keys in PATTERNS against SDLC_STAGES (existing PATTERNS dict structure unchanged; this is documentation/validation use only).

Usage in `sdlc-context.py` — STAGE_KEYWORDS dict keys must be a subset of SDLC_STAGES (no code change needed; SDLC_STAGES provides single source of truth).

**2. parse_roadmap_now() warn_on_empty:**
```python
def parse_roadmap_now(roadmap_path, warn_on_empty: bool = False) -> list:
    """Extract items from the ## Now section.

    If warn_on_empty=True and the file exists but the Now section is absent
    or empty, prints a warning to stderr.
    """
    path = Path(roadmap_path)
    items = parse_roadmap_section(path, "now")
    if warn_on_empty and path.exists() and not items:
        print("[zie-framework] WARNING: ROADMAP.md Now section is empty or missing",
              file=sys.stderr)
    return items
```

Callers: existing callers pass no argument (default False = no change). Only hooks that want the warning opt in.

**3. TEST_INDICATORS from .config:**

BEFORE:
```python
TEST_INDICATORS = ("test_", "_test.", ".test.", ".spec.")
```

AFTER:
```python
def _load_test_indicators(cwd: Path) -> tuple:
    config = load_config(cwd)
    raw = config.get("test_indicators", "")
    if raw:
        return tuple(s.strip() for s in raw.split(",") if s.strip())
    return ("test_", "_test.", ".test.", ".spec.")

# In main flow (after cwd is established):
TEST_INDICATORS = _load_test_indicators(cwd)
```

Config example (`zie-framework/.config`):
```json
{
  "test_indicators": "test_, _test., .test., .spec., _spec."
}
```

When key is absent or empty, falls back to the current hardcoded tuple (backward compatible).

**4. Async hooks in hooks.json:**

BEFORE:
```json
{
  "type": "command",
  "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\""
},
{
  "type": "command",
  "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\""
}
```

AFTER:
```json
{
  "type": "command",
  "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\"",
  "async": true
},
{
  "type": "command",
  "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\"",
  "async": true
}
```

notification-log.py is NOT made async — it is on the Notification event; future output handling (permission decisions) may depend on its response.

**5. hook-events.schema.json:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Claude Code Hook Event Envelope",
  "description": "Common envelope for all zie-framework hook event inputs (stdin JSON)",
  "type": "object",
  "properties": {
    "tool_name": {
      "type": "string",
      "description": "Name of the tool being invoked (PreToolUse/PostToolUse)"
    },
    "tool_input": {
      "type": ["object", "null"],
      "description": "Tool input parameters — shape varies by tool_name"
    },
    "tool_response": {
      "type": ["object", "string", "null"],
      "description": "Tool output (PostToolUse only)"
    },
    "is_interrupt": {
      "type": "boolean",
      "description": "True when Claude was interrupted mid-response"
    },
    "session_id": {
      "type": "string",
      "description": "Unique session identifier"
    }
  },
  "additionalProperties": true
}
```

**Edge Cases:**
- `SDLC_STAGES` import in intent-detect.py and sdlc-context.py adds a utils import but the stage name validation is passive (no runtime assertion — just a comment linking the two). Keeps hooks decoupled.
- `warn_on_empty=False` default: all existing callers are unaffected. Only hooks that explicitly opt in see the warning. No behavior change to existing hooks.
- `_load_test_indicators(cwd)` is a module-level initialization in task-completed-gate.py — runs once per hook invocation (hooks are short-lived processes). No caching needed.
- `load_config()` fix (consolidate-utils-patterns spec) must be implemented before `_load_test_indicators` can correctly read JSON values. The architecture-cleanup spec depends on consolidate-utils-patterns.
- Async session-learn: the hook writes `pending_learn.txt` and optionally calls the zie-memory API. Both are fire-and-forget from Claude's perspective — async is safe.
- Async session-cleanup: globs /tmp and removes old session files. Pure side effect, no output used by Claude — async is safe.
- hook-events.schema.json `additionalProperties: true` — the schema documents known fields without restricting unknown ones (Claude Code may add new fields in future versions).

**Out of Scope:**
- **Git status caching (M3)**: Each hook event type dispatches to different hooks; git calls are not "6 per event" but "1 per hook per event type". Cross-process caching via /tmp adds complexity (TTL management, cache invalidation) disproportionate to the ~2ms git status calls on local repos.
- **safety_check_agent.py default mode documentation (M8)**: The `load_config()` JSON fix (consolidate-utils-patterns) makes `safety_check_mode` readable from `.config` for the first time. The behavior (default to regex mode) is already correct in code and in the `.config.template`. No separate fix needed here.
- Making notification-log.py async — it runs on permission events where future output handling may matter
- Adding a `STAGE_COMMANDS` map to utils — `sdlc-context.py` is the only consumer; not worth extracting
