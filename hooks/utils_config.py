#!/usr/bin/env python3
"""Config loading and validation for zie-framework hooks."""
import json
import sys
from pathlib import Path

CONFIG_SCHEMA: dict = {
    "subprocess_timeout_s": (5, int),
    "safety_agent_timeout_s": (30, int),
    "auto_test_max_wait_s": (15, int),
    "auto_test_timeout_ms": (30000, int),
    "compact_hint_threshold": (0.8, float),
    "playwright_enabled": (False, bool),
}

CONFIG_DEFAULTS: dict = {
    "safety_check_mode": "regex",
    "test_runner": "",
    "auto_test_debounce_ms": 3000,
    "auto_test_timeout_ms": 30000,
    "test_indicators": "",
    "project_type": "unknown",
    "zie_memory_enabled": False,
}


def validate_config(config: dict) -> dict:
    """Fill all CONFIG_SCHEMA keys with typed defaults.

    Missing keys → filled with schema default (no warning).
    Wrong-type keys → replaced with schema default (warning emitted).
    None input → treated as {}.
    Returns a new dict with all schema keys guaranteed present and correctly typed.
    """
    if config is None:
        config = {}
    result = dict(config)
    wrong_type_keys = []
    for key, (default, expected_type) in CONFIG_SCHEMA.items():
        if key not in result:
            result[key] = default
        elif not isinstance(result[key], expected_type):
            wrong_type_keys.append(key)
            result[key] = default
    if wrong_type_keys:
        print(
            f"[zie-framework] config: defaulted keys: {', '.join(wrong_type_keys)}",
            file=sys.stderr,
        )
    return result


def load_config(cwd: Path) -> dict:
    """Read zie-framework/.config as JSON and return a validated dict.

    Merges CONFIG_DEFAULTS first, then loaded values, then validates CONFIG_SCHEMA
    keys for type safety. Always returns a fully-typed dict with all known keys.
    Absent file returns all defaults silently. Parse errors logged to stderr.
    """
    config_path = cwd / "zie-framework" / ".config"
    try:
        raw = json.loads(config_path.read_text())
        if not isinstance(raw, dict):
            raise TypeError(f"config must be a JSON object, got {type(raw).__name__}")
        merged = {**CONFIG_DEFAULTS, **raw}
        return validate_config(merged)
    except FileNotFoundError:
        return validate_config(dict(CONFIG_DEFAULTS))
    except Exception as e:
        print(f"[zie-framework] config parse error: {e}", file=sys.stderr)
        return validate_config(dict(CONFIG_DEFAULTS))
