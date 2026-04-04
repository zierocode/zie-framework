#!/usr/bin/env python3
"""PostToolUse:Edit/Write hook — checkpoint WIP to zie-memory every 5 edits."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import call_zie_memory_api, get_cwd, read_event
from utils_io import persistent_project_path, safe_write_persistent
from utils_roadmap import parse_roadmap_now

# Outer guard — any unhandled exception exits 0 (never blocks Claude)
try:
    event = read_event()

    tool_name = event.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    # Only run if zie-memory is available
    api_key = os.environ.get("ZIE_MEMORY_API_KEY", "")
    api_url = os.environ.get("ZIE_MEMORY_API_URL", "")
    if not api_key:
        sys.exit(0)
    if not api_url.startswith("https://"):
        sys.exit(0)

    # Fast-path: honour ZIE_MEMORY_ENABLED=0 injected by session-resume.py
    _mem_enabled = os.environ.get("ZIE_MEMORY_ENABLED", "").strip()
    if _mem_enabled == "0":
        sys.exit(0)

    cwd = get_cwd()
    zf = cwd / "zie-framework"
    if not zf.exists():
        sys.exit(0)

    # Edit counter via persistent file (survives session restart)
    counter_file = persistent_project_path("edit-count", cwd.name)
    count = 0
    if counter_file.exists():
        try:
            count = int(counter_file.read_text().strip())
        except Exception as e:
            print(f"[zie-framework] wip-checkpoint: {e}", file=sys.stderr)

    count += 1
    safe_write_persistent(counter_file, str(count))

    # Only checkpoint every 5 edits
    CHECKPOINT_EVERY = 5
    if count % CHECKPOINT_EVERY != 0:
        sys.exit(0)

    # Read current ROADMAP "Now" section for WIP context
    roadmap_file = zf / "ROADMAP.md"
    lines = parse_roadmap_now(roadmap_file)
    wip_summary = "; ".join(lines[:3]) if lines else ""

    if not wip_summary:
        sys.exit(0)

    project = cwd.name
    content = f"[WIP:{project}] {wip_summary} (checkpoint at {count} edits)"

    try:
        call_zie_memory_api(api_url, api_key, "/api/hooks/wip-update", {
            "content": content,
            "priority": "project",
            "tags": ["wip", "checkpoint", project],
            "project": project,
            "force": True,
        }, timeout=3)
    except Exception as e:
        print(f"[zie-framework] wip-checkpoint: {e}", file=sys.stderr)

except Exception:
    sys.exit(0)
