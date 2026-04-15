#!/usr/bin/env python3
"""Stop hook — clean up session-scoped caches and /tmp files on session end."""
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path, safe_project_name
from utils_cache import get_cache_manager

event = read_event()

cwd = get_cwd()
safe_project = safe_project_name(cwd.name)

# ── CacheManager session cleanup ──────────────────────────────────────────────
_session_id = event.get("session_id", "")
if _session_id:
    try:
        cache = get_cache_manager(cwd)
        cache.clear_session(_session_id)
    except Exception as e:
        print(f"[zf] session-cleanup: cache clear failed: {e}", file=sys.stderr)

# ── /tmp file cleanup (legacy + remaining /tmp flags) ─────────────────────────
# Remove project-scoped /tmp files. Persistent data under $CLAUDE_PLUGIN_DATA
# is intentionally excluded — it must survive session restart.
for tmp_file in Path(tempfile.gettempdir()).glob(f"zie-{safe_project}-*"):
    try:
        tmp_file.unlink()
    except Exception as e:
        print(f"[zf] session-cleanup: {e}", file=sys.stderr)