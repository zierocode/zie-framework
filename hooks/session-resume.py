#!/usr/bin/env python3
"""SessionStart hook — inject current SDLC state for instant session orientation."""
import sys
import json
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import parse_roadmap_now

try:
    event = json.loads(sys.stdin.read())
except Exception:  # intentional — malformed event must not crash hook
    sys.exit(0)

cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
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

# Read ROADMAP (truncated to avoid overloading context)
roadmap_text = ""
roadmap_file = zf / "ROADMAP.md"
if roadmap_file.exists():
    raw_lines = roadmap_file.read_text().splitlines()
    if len(raw_lines) > 200:
        raw_lines = raw_lines[:100]
    roadmap_text = "\n".join(raw_lines)

# Parse ROADMAP sections
def parse_section(text, header):
    lines = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("##") and header.lower() in line.lower():
            in_section = True
            continue
        if line.startswith("##") and in_section:
            break
        if in_section and line.strip().startswith("- "):
            lines.append(line.strip())
    return lines

now_items = parse_roadmap_now(roadmap_file)
next_items = parse_section(roadmap_text, "next")
done_items = parse_section(roadmap_text, "done")

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
