---
approved: true
approved_at: 2026-03-24
backlog: backlog/consolidate-utils-patterns.md
---

# Consolidate Duplicate Patterns into utils.py — Design Spec

**Problem:** Five hooks parse `.config` inline using `json.loads()` while `utils.load_config()` uses KEY=VALUE parsing — incompatible with the actual JSON `.config` format. This means `safety_check_mode` is never read from `.config` (silent bug). Additionally, the `re.sub(r'\s+', ' ', cmd.strip())` normalization pattern is duplicated across 4 hooks, and `safety_check_agent.py` has a 39-line importlib workaround to load BLOCKS from safety-check.py when they should be shared constants.

**Approach:** Three targeted changes to `hooks/utils.py` and affected hooks: (1) Fix `load_config()` to use `json.loads()` matching the actual `.config` format, then migrate 3 inline config loaders to use it; (2) Add `normalize_command(cmd)` to utils and migrate 4 callers; (3) Move BLOCKS/WARNS lists to utils and remove the importlib workaround in `safety_check_agent.py`. Leave `atomic_write()` and `_read_records()` unchanged — different semantics or single-file scope. Leave `is_zie_initialized()` extraction out of scope — trivial one-liner not worth a named function.

**Components:**

- `hooks/utils.py`
  - Fix `load_config()`: replace KEY=VALUE loop with `json.loads(config_path.read_text())`. Return `{}` on any error (same contract as before).
  - Add `normalize_command(cmd: str) -> str`: `re.sub(r'\s+', ' ', cmd.strip().lower())`
  - Add `BLOCKS: list` and `WARNS: list` — move from safety-check.py

- `hooks/safety-check.py`
  - Remove BLOCKS and WARNS list literals
  - Import `BLOCKS, WARNS` from utils
  - Update `evaluate()`: replace inline `re.sub(r'\s+', ' ', command.strip().lower())` with `normalize_command(command)`
  - Keep `evaluate()` function intact (called by safety_check_agent.py via importlib — until that's removed)

- `hooks/safety_check_agent.py`
  - Remove `_load_blocks()` function (39 lines + fallback inline list)
  - Remove module-level `BLOCKS = _load_blocks() + [...]`
  - Import `BLOCKS, normalize_command` from utils; extend locally for agent-specific patterns
  - Update `evaluate()`: replace inline `re.sub(...)` with `normalize_command()`
  - Remove `import importlib.util` (no longer needed)

- `hooks/auto-test.py`
  - Line 80: replace `config = json.loads(config_file.read_text())` with `config = load_config(cwd)` (import `load_config` from utils)
  - Remove manual `config_file = zf / ".config"; if config_file.exists()` guard (load_config handles missing file)

- `hooks/session-resume.py`
  - Line 24: same migration — replace inline `json.loads()` with `load_config(cwd)`

- `hooks/sdlc-compact.py`
  - Lines 79-84: replace inline `json.loads(config_path.read_text())` with `load_config(cwd)`

- `hooks/input-sanitizer.py`
  - Line 86: keep `normalized = re.sub(r"\s+", " ", command.strip())` as-is — input-sanitizer must preserve original case since the normalized command is passed to the confirmation prompt (display use). Add a comment: `# preserve case — display only, not pattern matching`. Do NOT use `normalize_command()` here.

- `hooks/sdlc-permissions.py`
  - Line 41: replace `cmd = re.sub(r'\s+', ' ', command.strip())` with `cmd = normalize_command(command)` (check if `.lower()` is needed here)

- `tests/unit/test_utils.py`
  - `TestLoadConfig` class: rewrite tests for JSON format (currently test KEY=VALUE parsing which will break)
  - Add `TestNormalizeCommand` class: parametrized tests for whitespace collapsing, lowercasing, strip
  - Update BLOCKS/WARNS import tests

**Data Flow — load_config() fix:**

BEFORE:
```python
def load_config(cwd: Path) -> dict:
    config_path = cwd / "zie-framework" / ".config"
    try:
        result = {}
        for line in config_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                result[key.strip()] = val.strip()
        return result
    except Exception:
        return {}
```

AFTER:
```python
def load_config(cwd: Path) -> dict:
    config_path = cwd / "zie-framework" / ".config"
    try:
        return json.loads(config_path.read_text())
    except Exception:
        return {}
```

**Data Flow — BLOCKS/WARNS move:**

Before: BLOCKS/WARNS defined in `safety-check.py`; `safety_check_agent.py` uses importlib to load them at module init with a 39-line fallback copy.

After: BLOCKS/WARNS defined in `utils.py`; both hooks import directly:
```python
# hooks/utils.py
BLOCKS = [
    (r"rm\s+-rf\s+(/\s|/\b|/$)", "rm -rf / is blocked..."),
    ...
]
WARNS = [
    (r"docker\s+compose\s+down\s+.*--volumes\b", "..."),
    ...
]

# hooks/safety_check_agent.py
from utils import get_cwd, load_config, read_event, BLOCKS, WARNS, normalize_command

_AGENT_BLOCKS = BLOCKS + [
    (r"curl\s+.*\|\s*bash\b", "curl pipe to bash blocked..."),
    (r"curl\s+.*\|\s*sh\b", "curl pipe to sh blocked..."),
    (r"wget\s+.*\|\s*bash\b", "wget pipe to bash blocked..."),
    (r"wget\s+.*\|\s*sh\b", "wget pipe to sh blocked..."),
]
```

**Data Flow — normalize_command:**

```python
# hooks/utils.py
def normalize_command(cmd: str) -> str:
    """Normalize whitespace and lowercase a shell command for pattern matching."""
    return re.sub(r'\s+', ' ', cmd.strip().lower())
```

Callers:
- `safety-check.py:evaluate()` — replaces `re.sub(r'\s+', ' ', command.strip().lower())`
- `safety_check_agent.py:evaluate()` — replaces `re.sub(r'\s+', ' ', command.strip().lower())`
- `sdlc-permissions.py` — replaces `re.sub(r'\s+', ' ', command.strip())` (verify `.lower()` is correct here)

**Edge Cases:**

- `load_config()` callers that previously used KEY=VALUE keys (e.g. `safety_check_mode`) now receive the JSON value as-is. JSON `"regex"` → Python string `"regex"`. JSON `false` → Python `False`. JSON `3000` → Python int `3000`. All downstream `.get("key", default)` calls work unchanged.
- `auto-test.py:76` — currently has `if not test_runner or not _debounce_env:` guard before reading config, then only reads if env vars absent. After migration, `load_config(cwd)` is called unconditionally (returns `{}` if missing). The env-var fast path still takes precedence since the guard uses env vars first.
- `sdlc-permissions.py` whitespace normalization: the original does NOT `.lower()`, but `normalize_command()` does. Verify against the patterns in `sdlc-permissions.py` — if patterns match case-insensitively already, adding `.lower()` is safe. If patterns rely on case, keep the inline version.
- `session-resume.py:load_config` migration: session-resume.py currently reads many JSON keys including booleans (`has_frontend`, `playwright_enabled`). These will work correctly with the new `json.loads()` based `load_config()`.
- Removing importlib from safety_check_agent.py: `import importlib.util` was the only importlib usage. Removing it reduces the hook's startup overhead slightly.
- BLOCKS/WARNS in utils.py: utils.py is imported by all hooks. Moving BLOCKS there means every hook that imports utils gets the lists — this is fine since they're pure data (no side effects).
- `_read_records()` in notification-log.py: single-file scope, called from two functions in the same file. Extracting to utils would make a private implementation detail public. Left as-is.
- `atomic_write()` vs `safe_write_tmp()`: `atomic_write()` raises on OSError; `safe_write_tmp()` catches and returns False. session-learn.py uses `atomic_write()` intentionally for reliable pending_learn writes. Not consolidated — different error semantics.

**Out of Scope:**
- `is_zie_initialized(cwd)` helper — `(cwd / "zie-framework").exists()` is self-documenting; adding a named function adds indirection without clarity
- `get_project_name(cwd)` helper — `cwd.name` is idiomatic Python, no wrapping needed
- `_read_records()` extraction — single-file helper, extracting to utils would expose private detail
- Migrating `atomic_write()` to `safe_write_tmp()` — different error semantics; callers rely on the difference
- `subagent-context.py` normalization variant (uses `-` not space) — different purpose, not a duplicate
- `input-sanitizer.py` normalization — must preserve original case for display; not a duplicate of normalize_command
