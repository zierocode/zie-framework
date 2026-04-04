#!/usr/bin/env python3
"""Stop hook — store session learnings in zie-memory and write pending_learn."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import call_zie_memory_api, get_cwd, read_event
from utils_io import atomic_write, persistent_project_path
from utils_roadmap import parse_roadmap_now

# Outer guard — any unhandled exception exits 0 (never blocks Claude)
try:
    event = read_event()

    api_key = os.environ.get("ZIE_MEMORY_API_KEY", "")
    api_url = os.environ.get("ZIE_MEMORY_API_URL", "")
    cwd = get_cwd()
    zf = cwd / "zie-framework"

    if not zf.exists():
        sys.exit(0)

    project = cwd.name

    # Write pending_learn marker for next session (persistent across restarts)
    pending_learn_file = persistent_project_path("pending_learn.txt", project)

    # Read ROADMAP for context
    roadmap_file = zf / "ROADMAP.md"
    lines = parse_roadmap_now(roadmap_file)
    wip_context = "; ".join(lines[:3]) if lines else ""

    atomic_write(
        pending_learn_file,
        f"project={project}\n"
        f"wip={wip_context}\n",
    )

    # Fast-path: honour ZIE_MEMORY_ENABLED=0 injected by session-resume.py
    _mem_enabled = os.environ.get("ZIE_MEMORY_ENABLED", "").strip()
    if _mem_enabled == "0":
        sys.exit(0)

    # If zie-memory enabled, call session-stop endpoint
    if not api_key:
        sys.exit(0)
    if not api_url.startswith("https://"):
        sys.exit(0)

    try:
        call_zie_memory_api(api_url, api_key, "/api/hooks/session-stop", {
            "project": project,
            "wip_summary": wip_context,
        })
    except Exception as e:
        print(f"[zie-framework] session-learn: {e}", file=sys.stderr)

except Exception:
    sys.exit(0)
