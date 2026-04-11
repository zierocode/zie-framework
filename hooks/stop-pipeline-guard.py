#!/usr/bin/env python3
"""Stop hook — warn if sprint intent detected but no approved artifacts produced.

Synchronous (no background: true in hooks.json) — warning must be visible
before session closes.

Flow:
1. Check intent-sprint-flag; exit 0 if absent.
2. Scan zie-framework/specs/ + plans/ for today-modified files with approved:true.
3. Warn if neither found.
4. Delete flag (cleanup).
5. Always exit 0 — warning only, never blocks.
"""
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path

try:
    event = read_event()
except Exception:
    sys.exit(0)

try:
    cwd = get_cwd()
    project = cwd.name

    # Step 1: Check sprint flag
    sprint_flag = project_tmp_path("intent-sprint-flag", project)
    if not sprint_flag.exists():
        sys.exit(0)

    # Step 2: Check for zie-framework dir
    zf = cwd / "zie-framework"
    if not zf.exists():
        sprint_flag.unlink(missing_ok=True)
        sys.exit(0)

    # Step 3: Scan for today-approved artifacts
    today = date.today().isoformat()
    found_approved = False

    for subdir in ("specs", "plans"):
        target_dir = zf / subdir
        if not target_dir.exists():
            continue
        for md_file in target_dir.glob("*.md"):
            try:
                import datetime as _dt
                mtime = _dt.date.fromtimestamp(md_file.stat().st_mtime).isoformat()
                if mtime != today:
                    continue
                content = md_file.read_text()
                if re.search(r'^approved:\s*true\s*$', content, re.MULTILINE):
                    found_approved = True
                    break
            except Exception as _e:
                print(f"[zie-framework] stop-pipeline-guard: {_e}", file=sys.stderr)
                continue
        if found_approved:
            break

    # Step 4: Warn if no approved artifacts
    if not found_approved:
        print(
            "[zie-framework] sprint intent detected but no approved spec/plan found this session\n"
            "  → Run /spec <feature> then /plan <feature> before implementing"
        )

    # Step 5: Cleanup flag
    sprint_flag.unlink(missing_ok=True)

except Exception:
    sys.exit(0)
