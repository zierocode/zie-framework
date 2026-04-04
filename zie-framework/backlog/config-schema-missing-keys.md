# Add compact_hint_threshold and playwright_enabled to CONFIG_SCHEMA + CONFIG_DEFAULTS

## Problem

`utils_config.py` CONFIG_SCHEMA validates and type-coerces 4 keys, but `compact_hint_threshold` (float, used by `compact-hint.py`) and `playwright_enabled` (bool, used by `session-resume.py`) are absent from both CONFIG_SCHEMA and CONFIG_DEFAULTS. A user setting `"compact_hint_threshold": "0.9"` (string) gets a silent comparison failure that disables the compact hint — sessions run to context-full without any warning.

## Motivation

A misconfigured `compact_hint_threshold` silently wastes the entire purpose of the compact hint feature — sessions hit context limits without warning, causing expensive compaction events or lost context. The fix is a one-line addition to CONFIG_SCHEMA and CONFIG_DEFAULTS for each missing key.

## Rough Scope

- Add `compact_hint_threshold: (float, 0.8)` to CONFIG_SCHEMA in `utils_config.py`
- Add `playwright_enabled: (bool, False)` to CONFIG_SCHEMA
- Ensure CONFIG_DEFAULTS is consistent
- Add tests for type coercion of these keys
