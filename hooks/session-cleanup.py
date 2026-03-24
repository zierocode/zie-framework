#!/usr/bin/env python3
"""Stop hook — remove project-scoped /tmp files on session end."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe_project_name, read_event, get_cwd

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
