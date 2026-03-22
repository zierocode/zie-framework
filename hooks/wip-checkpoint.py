#!/usr/bin/env python3
"""PostToolUse:Edit/Write hook — checkpoint WIP to zie-memory every 5 edits."""
import sys
import json
import os
import urllib.request
from pathlib import Path

try:
    event = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

tool_name = event.get("tool_name", "")
if tool_name not in ("Edit", "Write"):
    sys.exit(0)

# Only run if zie-memory is available
api_key = os.environ.get("ZIE_MEMORY_API_KEY", "")
api_url = os.environ.get("ZIE_MEMORY_API_URL", "https://memory.zie-agent.cloud")
if not api_key:
    sys.exit(0)

cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
zf = cwd / "zie-framework"
if not zf.exists():
    sys.exit(0)

# Edit counter via temp file
counter_file = Path("/tmp/zie-framework-edit-count")
count = 0
if counter_file.exists():
    try:
        count = int(counter_file.read_text().strip())
    except Exception:
        pass

count += 1
counter_file.write_text(str(count))

# Only checkpoint every 5 edits
CHECKPOINT_EVERY = 5
if count % CHECKPOINT_EVERY != 0:
    sys.exit(0)

# Read current ROADMAP "Now" section for WIP context
roadmap_file = zf / "ROADMAP.md"
wip_summary = ""
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
            lines.append(line.strip().lstrip("- [ ]").lstrip("- [x]").strip())
    wip_summary = "; ".join(lines[:3]) if lines else ""

if not wip_summary:
    sys.exit(0)

project = cwd.name
content = f"[WIP:{project}] {wip_summary} (checkpoint at {count} edits)"

try:
    payload = json.dumps({
        "content": content,
        "priority": "project",
        "tags": ["wip", "checkpoint", project],
        "project": project,
        "force": True,
    }).encode()

    req = urllib.request.Request(
        f"{api_url}/api/hooks/wip-update",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=3)
except Exception:
    pass  # Never crash the hook
