#!/usr/bin/env python3
"""StopFailure hook — log API error events to a project-scoped /tmp file."""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

try:
    from utils_event import get_cwd, read_event, sanitize_log_field
    from utils_io import project_tmp_path, safe_project_name
    from utils_roadmap import parse_roadmap_now
    event = read_event()
except Exception:
    sys.exit(0)

try:
    error_type = sanitize_log_field(event.get("error_type", "unknown"))
    error_details = sanitize_log_field(event.get("error_details", ""))

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

    _STOP_MESSAGES = {
        "rate_limit": "Wait before resuming.",
        "billing_error": "Wait before resuming.",
        "context_limit": "Use /compact or start a new session.",
        "api_error": "",
    }
    if error_type in _STOP_MESSAGES:
        hint = _STOP_MESSAGES[error_type]
        suffix = f" {hint}" if hint else ""
        print(f"[zie-framework] Session stopped: {error_type}.{suffix}", file=sys.stderr)
except Exception as e:
    print(f"[zie-framework] stopfailure-log: {e}", file=sys.stderr)

sys.exit(0)
