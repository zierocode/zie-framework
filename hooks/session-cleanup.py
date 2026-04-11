#!/usr/bin/env python3
"""Stop hook — remove project-scoped /tmp files on session end."""
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path, safe_project_name

event = read_event()

cwd = get_cwd()
safe_project = safe_project_name(cwd.name)

# Session-scoped tmp dir only. Persistent data under $CLAUDE_PLUGIN_DATA is
# intentionally excluded — it must survive session restart.
for tmp_file in Path(tempfile.gettempdir()).glob(f"zie-{safe_project}-*"):
    try:
        tmp_file.unlink()
    except Exception as e:
        print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)

# Explicitly unlink session-context cache flag (spec: context-efficiency Area 2)
# The glob above already catches it; this explicit call satisfies the spec requirement.
_session_id = event.get("session_id", "")
if _session_id:
    _safe_sid = re.sub(r'[^a-zA-Z0-9]', '-', _session_id)
    _cache_flag = project_tmp_path(f"session-context-{_safe_sid}", safe_project)
    try:
        _cache_flag.unlink(missing_ok=True)
    except Exception as e:
        print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)

# Clean up roadmap cache dirs (zie-<session_id>/roadmap.cache)
for cache_dir in Path(tempfile.gettempdir()).glob("zie-*/"):
    roadmap_cache = cache_dir / "roadmap.cache"
    if roadmap_cache.exists():
        try:
            roadmap_cache.unlink()
            if not any(cache_dir.iterdir()):
                cache_dir.rmdir()
        except Exception as e:
            print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)
