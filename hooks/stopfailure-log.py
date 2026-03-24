#!/usr/bin/env python3
"""StopFailure hook — log API error events to a project-scoped /tmp file."""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

try:
    from utils import get_cwd, parse_roadmap_now, project_tmp_path, read_event, safe_project_name
    event = read_event()
except Exception:
    sys.exit(0)

try:
    error_type = event.get("error_type", "unknown")
    error_details = event.get("error_details", "")

    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)

    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
    wip_lines = parse_roadmap_now(roadmap_path)
    wip_summary = " | ".join(wip_lines[:3])

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = f"[{ts}] error_type={error_type} wip={wip_summary} details={error_details}\n"

    log_path = project_tmp_path("failure-log", safe_project_name(cwd.name))
    try:
        with open(log_path, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[zie-framework] stopfailure-log: {e}", file=sys.stderr)
        sys.exit(0)

    if error_type in {"rate_limit", "billing_error"}:
        print(
            f"[zie-framework] Session stopped: {error_type}. Wait before resuming.",
            file=sys.stderr,
        )
except Exception as e:
    print(f"[zie-framework] stopfailure-log: {e}", file=sys.stderr)

sys.exit(0)
