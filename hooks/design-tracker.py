#!/usr/bin/env python3
"""UserPromptSubmit hook — detect design-intent signals and write design-mode flag.

Async (background: true in hooks.json) — never blocks Claude.
Checks for design signals in the user's message; writes a session flag that
stop-capture.py reads at Stop time to write .zie/handoff.md.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_cache import get_cache_manager
from utils_error import log_error
from utils_event import get_cwd, read_event

DESIGN_SIGNALS = [
    r"\bdesign\b",
    r"\bspec\b",
    r"\bfeature\b",
    r"\bimprove\b",
    r"discuss.*sprint",
    r"let.*s build",
    r"what if",
    r"\barchitect",
    r"สร้าง.*ใหม่",
    r"ออกแบบ",
    r"วางแผน.*สร้าง",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in DESIGN_SIGNALS]


try:
    event = read_event()
except (json.JSONDecodeError, OSError):
    sys.exit(0)

try:
    message = (event.get("prompt") or "").strip()
    if not message or len(message) < 5:
        sys.exit(0)

    session_id = event.get("session_id", "")
    cwd = get_cwd()

    hits = sum(1 for p in _COMPILED if p.search(message))
    if hits < 2:
        sys.exit(0)

    cache = get_cache_manager(cwd)
    try:
        cache.set_flag("design-mode", session_id or "default")
    except Exception as _e:
        print(f"[zf] design-tracker: flag write failed: {_e}", file=sys.stderr)

except Exception as e:
    log_error("design-tracker", "main", e)
    sys.exit(0)
