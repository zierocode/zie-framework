#!/usr/bin/env python3
"""Stop hook — two-tier context window health monitor.

Tiers (each fires once per session):
  75% advisory_threshold  → gentle hint: "consider /compact soon"
  90% mandatory_threshold → hard warning: "start fresh session"

Uses session-scoped flags to avoid repeated nagging within a session.
Always exits 0 (ADR-003).
Infinite-loop guard: exits immediately when stop_hook_active is truthy.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_config import load_config
from utils_io import project_tmp_path

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

    advisory_threshold = config.get("compact_advisory_threshold", 0.75)
    mandatory_threshold = config.get("compact_mandatory_threshold", 0.90)

    context_window = event.get("context_window")
    if not isinstance(context_window, dict):
        sys.exit(0)

    current = context_window.get("current_tokens")
    max_tokens = context_window.get("max_tokens")
    if current is None or not max_tokens:
        sys.exit(0)

    pct = current / max_tokens
    pct_int = int(pct * 100)

    # Session-scoped once-per-tier flags
    session_id = event.get("session_id", "")
    safe_sid = re.sub(r'[^a-zA-Z0-9]', '-', session_id) if session_id else "nosid"
    project = cwd.name

    def _tier_fired(tier: str) -> bool:
        flag = project_tmp_path(f"compact-tier-{tier}-{safe_sid}", project)
        return flag.exists()

    def _mark_tier(tier: str) -> None:
        flag = project_tmp_path(f"compact-tier-{tier}-{safe_sid}", project)
        try:
            flag.write_text("fired")
        except Exception as _e:
            print(f"[zie-framework] compact-hint: flag write failed: {_e}", file=sys.stderr)

    if pct >= mandatory_threshold:
        if not _tier_fired("mandatory"):
            print(
                f"[zie-framework] Context at {pct_int}% \u2014 too full for heavy commands."
                " Start a fresh session instead: run `make zie-release` in a new terminal"
                " for release, or open a new Claude window for other commands."
            )
            _mark_tier("mandatory")
    elif pct >= advisory_threshold:
        if not _tier_fired("advisory"):
            print(
                f"[zie-framework] Context at {pct_int}%"
                " \u2014 consider /compact soon to stay efficient."
            )
            _mark_tier("advisory")

except Exception as e:
    print(f"[zie-framework] compact-hint: {e}", file=sys.stderr)
sys.exit(0)
