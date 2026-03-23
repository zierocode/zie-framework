#!/usr/bin/env python3
"""Stop hook — store session learnings in zie-memory and write pending_learn."""
import sys
import json
import os
import urllib.request
from pathlib import Path

try:
    event = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

api_key = os.environ.get("ZIE_MEMORY_API_KEY", "")
api_url = os.environ.get("ZIE_MEMORY_API_URL", "")
cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
zf = cwd / "zie-framework"

if not zf.exists():
    sys.exit(0)

project = cwd.name

# Write pending_learn marker for next session
pending_learn_file = Path.home() / ".claude" / "projects" / project / "pending_learn.txt"
pending_learn_file.parent.mkdir(parents=True, exist_ok=True)

# Read ROADMAP for context
roadmap_file = zf / "ROADMAP.md"
wip_context = ""
if roadmap_file.exists():
    text = roadmap_file.read_text()
    lines = []
    in_now = False
    for line in text.splitlines():
        if line.startswith("##") and "now" in line.lower():
            in_now = True
            continue
        if line.startswith("##") and in_now:
            break
        if in_now and line.strip().startswith("- "):
            import re
            clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line.strip())
            lines.append(clean.lstrip("- [ ]").lstrip("- [x]").strip())
    wip_context = "; ".join(lines[:3]) if lines else ""

pending_learn_file.write_text(
    f"project={project}\n"
    f"wip={wip_context}\n"
)

# If zie-memory enabled, call session-stop endpoint
if not api_key:
    sys.exit(0)
if not api_url.startswith("https://"):
    sys.exit(0)

try:
    payload = json.dumps({
        "project": project,
        "wip_summary": wip_context,
    }).encode()

    req = urllib.request.Request(
        f"{api_url}/api/hooks/session-stop",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=5)
except Exception:
    pass  # Never crash on stop
