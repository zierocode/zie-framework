---
approved: false
approved_at: null
backlog: null
---

# Proactive Compact Hint — Design Spec

**Problem:** When context usage climbs high, Claude Code silently approaches the compaction threshold. Users have no early warning to run `/compact` proactively, so they get forced compaction at a bad moment (mid-TDD loop, mid-plan) rather than choosing a clean break point.

**Approach:** Extend the Stop hook to inspect the `context_window` field in the hook event JSON. If `current_tokens / max_tokens` meets or exceeds a configurable threshold (default 80%), print a plain-text hint to stdout. Plain text output from a Stop hook is surfaced to Claude as informational context — no `decision: block` needed and no re-invoke triggered. The hook always exits 0.

**Components:**

- Create: `hooks/compact-hint.py` — Stop hook; reads `context_window` from event; computes usage %; prints hint when threshold met; exits 0 on all paths
- Modify: `hooks/hooks.json` — register `compact-hint.py` for the `Stop` event
- Modify: `CLAUDE.md` — document `.config` key `compact_hint_threshold`
- Create: `tests/test_compact_hint.py` — unit tests: above threshold, below threshold, field missing, threshold from config

**Data Flow:**

1. Claude Code fires `Stop`; stdin delivers event JSON which may include `{"context_window": {"current_tokens": N, "max_tokens": M}, ...}`
2. `read_event()` parses stdin → `event` dict; outer guard exits 0 on any parse failure
3. `get_cwd()` → `cwd`; `load_config(cwd)` → `config`; read `compact_hint_threshold` (default `0.8`)
4. Extract `context_window = event.get("context_window")`; if missing or not a dict, exit 0 silently
5. Extract `current_tokens = context_window.get("current_tokens")` and `max_tokens = context_window.get("max_tokens")`; if either is missing or `max_tokens` is 0, exit 0 silently
6. Compute `pct = current_tokens / max_tokens`
7. If `pct >= threshold`: print `[zie-framework] Context at {int(pct * 100)}% — consider running /compact to free space before continuing.` to stdout; exit 0
8. If `pct < threshold`: exit 0 silently

**Hook Pattern (two-tier):**

```python
# Outer guard
try:
    event = read_event()
    if event.get("stop_hook_active"):
        sys.exit(0)
except Exception:
    sys.exit(0)

# Inner operations
try:
    cwd = get_cwd()
    config = load_config(cwd)
    threshold = config.get("compact_hint_threshold", 0.8)
    context_window = event.get("context_window")
    if not isinstance(context_window, dict):
        sys.exit(0)
    current = context_window.get("current_tokens")
    max_tokens = context_window.get("max_tokens")
    if current is None or not max_tokens:
        sys.exit(0)
    pct = current / max_tokens
    if pct >= threshold:
        print(f"[zie-framework] Context at {int(pct * 100)}% — consider running /compact to free space before continuing.")
except Exception as e:
    print(f"[zie-framework] compact-hint: {e}", file=sys.stderr)
sys.exit(0)
```

**Configuration:**

`.config` key `compact_hint_threshold` (float, default `0.8`). Follows the existing `load_config()` pattern from `utils.py`.

CLAUDE.md `.config` table entry:

| `compact_hint_threshold` | `0.8` | `float` | Usage fraction (0.0–1.0) at which the Stop hook prints the `/compact` hint. Set to `1.0` to disable. |

**Edge Cases:**

- `context_window` field absent from event (e.g., older Claude Code version or TaskCompleted): skip silently; this is why we target Stop only — TaskCompleted may not provide this field
- `max_tokens` is `0` or missing: division guard prevents ZeroDivisionError; exits 0 silently
- `current_tokens` exceeds `max_tokens` (> 100%): prints hint with >100% value — still valid and actionable
- `stop_hook_active` is set: exit immediately (standard infinite-loop guard already in Stop hook pattern)
- `compact_hint_threshold` absent from `.config`: defaults to `0.8` via `config.get()`
- `compact_hint_threshold` set to `1.0`: threshold never met in practice; effectively disables the hint
- `.config` missing or unparseable: `load_config()` returns defaults; hook proceeds with default threshold

**Why Stop Only (not TaskCompleted):**

The `Stop` event fires after every Claude response, reliably including the `context_window` field. `TaskCompleted` fires on session end and may not carry context usage data. Hooking Stop ensures the hint fires while the user is still actively working and can act on it.

**Why stdout (not decision:block):**

The hint is informational. Using `decision: block` would force a re-invoke and interrupt flow — far too intrusive for a nudge. Plain text on stdout is surfaced as context to Claude without triggering any special behavior.

**Out of Scope:**

- Auto-running `/compact` (user must trigger manually)
- Tracking context trend across multiple Stop events
- Suppressing the hint after it fires once per session
- Adjusting threshold dynamically based on task type
- Supporting the TaskCompleted event

**Acceptance Criteria:**

1. Hint is printed to stdout when `current_tokens / max_tokens >= compact_hint_threshold`
2. No output when `current_tokens / max_tokens < compact_hint_threshold`
3. No output when `context_window` field is absent from the event
4. Hook always exits 0 — never exits with a non-zero code
5. `compact_hint_threshold` is read from `.config`; defaults to `0.8` when absent
6. Hint message format: `[zie-framework] Context at {pct}% — consider running /compact to free space before continuing.`

**Tests (`tests/test_compact_hint.py`):**

- `test_hint_printed_above_threshold`: event with `current_tokens=850`, `max_tokens=1000` (85%) → hint printed to stdout
- `test_no_output_below_threshold`: event with `current_tokens=700`, `max_tokens=1000` (70%) → no stdout output
- `test_no_output_at_exactly_threshold`: event with `current_tokens=800`, `max_tokens=1000` (80%) → hint printed (boundary: >=)
- `test_no_output_missing_context_window`: event without `context_window` key → no stdout output, exits 0
- `test_no_output_missing_tokens`: event with `context_window={}` → no stdout output, exits 0
- `test_custom_threshold_from_config`: threshold set to `0.9` in config; event at 85% → no hint; event at 91% → hint
- `test_stop_hook_active_guard`: event with `stop_hook_active: true` → exits 0 immediately, no hint
