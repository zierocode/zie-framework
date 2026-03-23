#!/usr/bin/env python3
"""Stop hook — remove project-scoped /tmp files on session end."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe_project_name

try:
    event = json.loads(sys.stdin.read())
except Exception:
    # intentional — malformed event must not crash hook
    sys.exit(0)

cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
safe_project = safe_project_name(cwd.name)

for tmp_file in Path("/tmp").glob(f"zie-{safe_project}-*"):  # nosec B108 — project-scoped /tmp paths by design
    try:
        tmp_file.unlink()
    except Exception as e:
        print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)
