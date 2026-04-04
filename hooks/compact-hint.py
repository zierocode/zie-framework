#!/usr/bin/env python3
"""Stop hook — print a /compact hint when context usage meets the threshold.

Reads context_window.current_tokens / max_tokens from the Stop event JSON.
If the ratio >= compact_hint_threshold (default 0.8 from .config), prints
a plain-text hint to stdout. Plain text on stdout is surfaced to Claude as
informational context — no decision:block needed.

Always exits 0 (ADR-003).
Infinite-loop guard: exits immediately when stop_hook_active is truthy.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_config import load_config

# ---------------------------------------------------------------------------
# Outer guard — parse stdin; never block Claude on failure
# ---------------------------------------------------------------------------
try:
    event = read_event()
    if event.get("stop_hook_active"):
        sys.exit(0)
except Exception:
    sys.exit(0)

# ---------------------------------------------------------------------------
# Inner operations — check context usage; print hint when threshold met
# ---------------------------------------------------------------------------
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
        print(
            f"[zie-framework] Context at {int(pct * 100)}%"
            " \u2014 consider running /compact to free space before continuing."
        )
except Exception as e:
    print(f"[zie-framework] compact-hint: {e}", file=sys.stderr)
sys.exit(0)
