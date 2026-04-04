# Plan: Add compact_hint_threshold and playwright_enabled to CONFIG_SCHEMA

status: approved

## Tasks

### 1. RED — write failing tests in `tests/unit/test_utils_config.py`

Create `tests/unit/test_utils_config.py` with the following test cases:

- `test_compact_hint_threshold_in_schema` — assert `"compact_hint_threshold"` is a key in `CONFIG_SCHEMA`.
- `test_playwright_enabled_in_schema` — assert `"playwright_enabled"` is a key in `CONFIG_SCHEMA`.
- `test_compact_hint_threshold_in_defaults` — assert `"compact_hint_threshold"` is a key in `CONFIG_DEFAULTS` with value `0.8`.
- `test_playwright_enabled_in_defaults` — assert `"playwright_enabled"` is a key in `CONFIG_DEFAULTS` with value `False`.
- `test_string_threshold_coerced_to_default` — call `validate_config({"compact_hint_threshold": "0.9"})`, assert result `"compact_hint_threshold"` equals `0.8` (schema default, not the string value).
- `test_float_threshold_kept` — call `validate_config({"compact_hint_threshold": 0.9})`, assert result `"compact_hint_threshold"` equals `0.9`.
- `test_string_playwright_enabled_coerced_to_default` — call `validate_config({"playwright_enabled": "true"})`, assert result `"playwright_enabled"` is `False`.
- `test_bool_playwright_enabled_kept` — call `validate_config({"playwright_enabled": True})`, assert result `"playwright_enabled"` is `True`.
- `test_load_config_missing_file_has_threshold_default` — call `load_config(tmp_path)` (no `.config` file), assert `"compact_hint_threshold"` equals `0.8`.
- `test_load_config_missing_file_has_playwright_default` — call `load_config(tmp_path)` (no `.config` file), assert `"playwright_enabled"` is `False`.

Run `make test-fast` — all new tests should fail (RED).

### 2. GREEN — update `hooks/utils_config.py`

Add to `CONFIG_SCHEMA`:

```python
"compact_hint_threshold": (0.8, float),
"playwright_enabled": (False, bool),
```

Add to `CONFIG_DEFAULTS`:

```python
"compact_hint_threshold": 0.8,
"playwright_enabled": False,
```

Run `make test-fast` — all new tests should pass (GREEN).

### 3. REFACTOR — verify no inline defaults remain

Check that `compact-hint.py` and `session-resume.py` still use their `.get(key, default)` fallback calls (they do — no change needed). The inline defaults in those hooks are now redundant but harmless; leave them as defensive fallbacks per existing hook style.

Run `make lint` — no lint issues expected.

### 4. Full gate

Run `make test-ci` — full suite with coverage gate must pass before commit.

## Files to Change

| File | Change |
| --- | --- |
| `hooks/utils_config.py` | Add `compact_hint_threshold` and `playwright_enabled` to `CONFIG_SCHEMA` and `CONFIG_DEFAULTS` |
| `tests/unit/test_utils_config.py` | Create — new test file covering schema membership, type coercion, and load_config defaults |
