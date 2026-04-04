# Spec: Add compact_hint_threshold and playwright_enabled to CONFIG_SCHEMA

status: draft

## Problem

`utils_config.py` validates and type-coerces keys declared in `CONFIG_SCHEMA`, but two keys used by hooks are absent:

- `compact_hint_threshold` — used by `compact-hint.py`. A user setting `"compact_hint_threshold": "0.9"` (string) gets a silent type mismatch: `"0.9" >= 0.8` evaluates to `True` in Python (string vs float), but the comparison semantics are wrong and fragile. More critically, the key receives no default coercion guarantee, so any future stricter check could silently disable the feature.
- `playwright_enabled` — used by `session-resume.py` (`_check_playwright_version`). Without a schema entry, a string `"true"` (from JSON editing mistakes) is truthy and bypasses the `not config.get("playwright_enabled")` guard, potentially spawning an unwanted subprocess.

Neither key is in `CONFIG_DEFAULTS` either, so `load_config` does not guarantee their presence after the merge step.

## Solution

1. Add `"compact_hint_threshold": (0.8, float)` to `CONFIG_SCHEMA` in `utils_config.py`.
2. Add `"playwright_enabled": (False, bool)` to `CONFIG_SCHEMA`.
3. Add both keys to `CONFIG_DEFAULTS` with the same defaults (`0.8` and `False`).

This gives both keys the full validate_config treatment: missing → filled with default, wrong type → replaced with default + stderr warning.

No changes required to `compact-hint.py` or `session-resume.py` — they already call `load_config` and access the keys via `config.get(...)`.

## Acceptance Criteria

- `CONFIG_SCHEMA` contains `"compact_hint_threshold": (0.8, float)`.
- `CONFIG_SCHEMA` contains `"playwright_enabled": (False, bool)`.
- `CONFIG_DEFAULTS` contains `"compact_hint_threshold": 0.8`.
- `CONFIG_DEFAULTS` contains `"playwright_enabled": False`.
- `validate_config({"compact_hint_threshold": "0.9"})` returns `{"compact_hint_threshold": 0.8, ...}` (string coerced to default, warning emitted).
- `validate_config({"compact_hint_threshold": 0.9})` returns `{"compact_hint_threshold": 0.9, ...}` (valid float kept).
- `validate_config({"playwright_enabled": "true"})` returns `{"playwright_enabled": False, ...}` (string coerced to default).
- `validate_config({"playwright_enabled": True})` returns `{"playwright_enabled": True, ...}` (valid bool kept).
- `load_config` on a missing `.config` file returns a dict with both keys at their defaults.
- All existing tests continue to pass.

## Out of Scope

- Changing how `compact-hint.py` reads the threshold (it already works correctly once the schema is present).
- Adding numeric range validation (e.g., 0.0–1.0 for threshold) — not needed for this fix.
- Adding new config keys beyond the two identified.
