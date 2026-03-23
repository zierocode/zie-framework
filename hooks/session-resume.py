#!/usr/bin/env python3
"""SessionStart hook — inject current SDLC state for instant session orientation."""
import sys
import json
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import parse_roadmap_now, parse_roadmap_section, read_event, get_cwd

event = read_event()

cwd = get_cwd()
zf = cwd / "zie-framework"

if not zf.exists():
    sys.exit(0)

# Read config
config = {}
config_file = zf / ".config"
if config_file.exists():
    try:
        config = json.loads(config_file.read_text())
    except Exception as e:
        print(f"[zie] warning: .config unreadable ({e}), using defaults", file=sys.stderr)

roadmap_file = zf / "ROADMAP.md"
now_items = parse_roadmap_now(roadmap_file)
next_items = parse_roadmap_section(roadmap_file, "next")

# Read VERSION
version = "?"
version_file = cwd / "VERSION"
if version_file.exists():
    version = version_file.read_text().strip()

# Get most recent plan
plans_dir = zf / "plans"
active_plan = None
if plans_dir.exists():
    plans = sorted(plans_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if plans:
        active_plan = plans[0].name

project_name = cwd.name
project_type = config.get("project_type", "unknown")
zie_memory = config.get("zie_memory_enabled", False)

lines = [
    f"[zie-framework] {project_name} ({project_type}) v{version}",
]

if now_items:
    active = now_items[0]
    lines.append(f"  Active  : {active}")
    if active_plan:
        lines.append(f"  Plan    : zie-framework/plans/{active_plan}")
    lines.append(f"  Backlog : {len(next_items)} items in Next")
else:
    lines.append("  No active feature — run /zie-backlog to start one")

lines.append(f"  Brain   : {'enabled' if zie_memory else 'disabled'}")
lines.append("  → Run /zie-status for full state")

print("\n".join(lines))
