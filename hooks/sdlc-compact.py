#!/usr/bin/env python3
"""PreCompact/PostCompact hook — persist and restore SDLC state across context compaction."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    get_cwd,
    load_config,
    parse_roadmap_section_content,
    project_tmp_path,
    read_event,
    read_roadmap_cached,
    safe_write_tmp,
)

# ---------------------------------------------------------------------------
# Outer guard — parse event; exit 0 on any failure; never block Claude
# ---------------------------------------------------------------------------
try:
    event = read_event()
    hook_event_name = event.get("hook_event_name", "")
    if hook_event_name not in ("PreCompact", "PostCompact"):
        sys.exit(0)

    cwd = get_cwd()
    zf = cwd / "zie-framework"
    if not zf.exists():
        sys.exit(0)

    project_name = cwd.name
    snap_path = project_tmp_path("compact-snapshot", project_name)
    session_id = event.get("session_id", "default")
except Exception:
    sys.exit(0)

# ---------------------------------------------------------------------------
# Inner operations — log errors to stderr; never raise; always exit 0
# ---------------------------------------------------------------------------

if hook_event_name == "PreCompact":
    # --- Collect active task and now_items from ROADMAP (via session cache) ---
    try:
        roadmap_path = zf / "ROADMAP.md"
        roadmap_content = read_roadmap_cached(roadmap_path, session_id)
        now_items = parse_roadmap_section_content(roadmap_content, "now")
        active_task = now_items[0] if now_items else ""
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: roadmap read failed: {e}", file=sys.stderr)
        now_items = []
        active_task = ""

    # --- Collect git branch ---
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        git_branch = result.stdout.strip()
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: git branch failed: {e}", file=sys.stderr)
        git_branch = ""

    # --- Collect changed files ---
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        changed_files = [f for f in result.stdout.splitlines() if f.strip()][:20]
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: git diff failed: {e}", file=sys.stderr)
        changed_files = []

    # --- Read tdd_phase from .config ---
    tdd_phase = load_config(cwd).get("tdd_phase", "")

    # --- Build and write snapshot ---
    snapshot = {
        "active_task": active_task,
        "now_items": now_items,
        "git_branch": git_branch,
        "changed_files": changed_files,
        "tdd_phase": tdd_phase,
    }
    try:
        safe_write_tmp(snap_path, json.dumps(snapshot))
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: snapshot write failed: {e}", file=sys.stderr)

elif hook_event_name == "PostCompact":
    # --- Read snapshot; fall back to live ROADMAP on any failure ---
    snapshot = None
    try:
        if snap_path.exists():
            snapshot = json.loads(snap_path.read_text())
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: snapshot read failed: {e}", file=sys.stderr)

    if snapshot is None:
        # Fallback: read live ROADMAP (via session cache)
        try:
            roadmap_content = read_roadmap_cached(zf / "ROADMAP.md", session_id)
            now_items = parse_roadmap_section_content(roadmap_content, "now")
            active_task = now_items[0] if now_items else ""
        except Exception as e:
            print(f"[zie-framework] sdlc-compact: fallback roadmap failed: {e}", file=sys.stderr)
            now_items = []
            active_task = ""
        snapshot = {
            "active_task": active_task,
            "now_items": now_items,
            "git_branch": "",
            "changed_files": [],
            "tdd_phase": "",
        }

    # --- Build context block ---
    try:
        lines = ["[zie-framework] SDLC state restored after context compaction."]
        if snapshot.get("active_task"):
            lines.append(f"Active task: {snapshot['active_task']}")
        if snapshot.get("now_items") and len(snapshot["now_items"]) > 1:
            lines.append("Now items:")
            for item in snapshot["now_items"]:
                lines.append(f"  - {item}")
        if snapshot.get("git_branch"):
            lines.append(f"Git branch: {snapshot['git_branch']}")
        if snapshot.get("tdd_phase"):
            lines.append(f"TDD phase: {snapshot['tdd_phase']}")
        if snapshot.get("changed_files"):
            lines.append("Changed files (since last commit):")
            for f in snapshot["changed_files"]:
                lines.append(f"  - {f}")
        context = "\n".join(lines)
        print(json.dumps({"additionalContext": context}))
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: context build failed: {e}", file=sys.stderr)
        print(json.dumps({"additionalContext": ""}))

if __name__ == "__main__":
    pass
