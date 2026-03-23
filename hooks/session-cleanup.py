#!/usr/bin/env python3
"""Stop hook — remove project-scoped /tmp files on session end."""
import json
import os
import re
import sys
from pathlib import Path

try:
    event = json.loads(sys.stdin.read())
except Exception:
    # intentional — malformed event must not crash hook
    sys.exit(0)

cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
safe_project = re.sub(r'[^a-zA-Z0-9]', '-', cwd.name)

for tmp_file in Path("/tmp").glob(f"zie-{safe_project}-*"):
    try:
        tmp_file.unlink()
    except Exception as e:
        print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)
