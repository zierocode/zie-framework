# Consolidate Duplicate Patterns into utils.py

**Source**: audit-2026-03-24b H6+H7 + M1+M2+M7+M9+M15 + L9 (Agents A,B,E)
**Effort**: M
**Score impact**: +16 High + +15 Medium + +1 Low = +32 (Lean + Quality lift)

## Problem

Multiple code patterns duplicated across hooks that should live in utils.py:

### 1. Inline config loading (H6) — 5 hooks
`auto-test.py:80`, `session-resume.py:24`, `sdlc-compact.py:81`,
`task-completed-gate.py:43`, `notification-log.py` all parse `.config` inline
with different error handling. `utils.load_config()` exists but only 2 hooks use it.

### 2. Whitespace normalization (H7) — 5 hooks
`re.sub(r'\s+', ' ', cmd.strip())` repeated in:
- `safety-check.py:47`
- `safety_check_agent.py:64`
- `input-sanitizer.py:86`
- `sdlc-permissions.py:41`
- `subagent-context.py:38` (variant)

Should be `utils.normalize_command(cmd)`.

### 3. Duplicate BLOCKS patterns (M1/M9) — importlib workaround
`safety_check_agent.py:18-39` dynamically imports BLOCKS from safety-check.py
via importlib with a 39-line fallback list. Fragile and adds 90+ LOC.
BLOCKS/WARNS should live in `utils.py` or a new `safety_constants.py`.

### 4. cwd.name / is_zie_initialized pattern (M2) — 13+ instances
Every hook checks `(get_cwd() / "zie-framework").exists()` and uses `cwd.name`.
Should be `utils.is_zie_initialized(cwd)` and `utils.get_project_name()`.

### 5. Config handling inconsistent (M7)
Different except behavior in auto-test.py vs session-resume.py when .config
is missing or corrupt. utils.load_config() should be the canonical path with
consistent silent fallback to `{}`.

### 6. Over-engineered single-use helpers (M15)
`safety_check_agent.py:_load_blocks()` and `notification-log.py:_read_records()`
are single-use functions adding 20+ LOC each without abstraction value.

### 7. atomic_write() vs safe_write_tmp semantics (L9)
Only `session-learn.py` calls `atomic_write()`. Verify it's equivalent to
`safe_write_tmp()` and consolidate if so.

## Scope

- Add to `hooks/utils.py`:
  - `normalize_command(cmd: str) -> str`
  - `is_zie_initialized(cwd: Path) -> bool`
  - `get_project_name(cwd: Path) -> str`
- Move BLOCKS/WARNS to `hooks/utils.py` or `hooks/safety_constants.py`
- Migrate all 5 inline config loaders to `utils.load_config()`
- Remove importlib workaround in safety_check_agent.py
- Inline or remove single-use helpers
- Verify and consolidate atomic_write vs safe_write_tmp

## Acceptance Criteria

- [ ] `normalize_command()` in utils, imported by all 5 callers
- [ ] `is_zie_initialized()` and `get_project_name()` in utils, used consistently
- [ ] BLOCKS/WARNS centralized, safety_check_agent.py importlib workaround removed
- [ ] All hooks use `utils.load_config()` for .config reading
- [ ] ~100 LOC reduction across hooks/
- [ ] All existing tests still pass
