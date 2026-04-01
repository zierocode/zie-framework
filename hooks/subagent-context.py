#!/usr/bin/env python3
"""SubagentStart hook — inject SDLC context into Explore/Plan subagents."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils import get_cwd, parse_roadmap_section_content, read_event, read_roadmap_cached

# ── Outer guard ───────────────────────────────────────────────────────────────

try:
    event = read_event()
    agent_type = event.get("agentType", "")
    if not re.search(r'Explore|Plan', agent_type, re.IGNORECASE):
        sys.exit(0)
    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Inner operations ──────────────────────────────────────────────────────────

feature_slug = "none"
active_task = "unknown"
adr_count = "unknown"
session_id = event.get("session_id", "default")

# Read ROADMAP Now lane (via session cache)
try:
    roadmap_content = read_roadmap_cached(cwd / "zie-framework" / "ROADMAP.md", session_id)
    now_items = parse_roadmap_section_content(roadmap_content, "now")
    if now_items:
        raw = now_items[0]
        slug = raw.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug).strip('-')
        feature_slug = slug if slug else "none"
    else:
        feature_slug = "none"
        active_task = "none"
except Exception as e:
    print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)

# Find most-recent plan file and extract first incomplete task
if feature_slug != "none" or active_task == "unknown":
    try:
        plans_dir = cwd / "zie-framework" / "plans"
        plan_files = sorted(
            plans_dir.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if plan_files:
            plan_text = plan_files[0].read_text()
            found = None
            for line in plan_text.splitlines():
                if re.search(r'- \[ \]', line):
                    found = line
                    break
            if found is not None:
                task = re.sub(r'^\s*-\s*\[\s*\]\s*', '', found)
                task = re.sub(r'\*\*', '', task).strip()
                active_task = task if task else "unknown"
            else:
                active_task = "all tasks complete"
        else:
            active_task = "unknown"
    except Exception as e:
        print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)

# Count ADRs from project/context.md
try:
    context_file = cwd / "zie-framework" / "project" / "context.md"
    if context_file.exists():
        text = context_file.read_text()
        adr_count = str(len(re.findall(r'^## ADR-\d+', text, re.MULTILINE)))
    else:
        adr_count = "unknown"
except Exception as e:
    print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)

# Emit additionalContext
payload = (
    f"[zie-framework] Active: {feature_slug} | "
    f"Task: {active_task} | "
    f"ADRs: {adr_count} (see zie-framework/project/context.md)"
)
print(json.dumps({"additionalContext": payload}))
