#!/usr/bin/env python3
"""PreCompact/PostCompact hook — persist and restore SDLC state across context compaction."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_cache import get_cache_manager
from utils_config import load_config
from utils_error import log_error
from utils_event import get_cwd, read_event
from utils_io import persistent_project_path, safe_write_persistent
from utils_roadmap import (
    get_cached_git_status,
    parse_roadmap_section_content,
    read_roadmap_cached,
    write_git_status_cache,
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
    session_id = event.get("session_id", "default")
    cache = get_cache_manager(cwd)
except (json.JSONDecodeError, OSError):
    sys.exit(0)
except Exception as e:
    log_error("sdlc-compact", "outer_guard", e)
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

    # --- Collect git branch (with session cache, 5s TTL) ---
    try:
        cached = get_cached_git_status(session_id, "branch")
        if cached is not None:
            git_branch = cached
        else:
            result = subprocess.run(
                ["git", "-C", str(cwd), "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            git_branch = result.stdout.strip()
            if result.returncode == 0 and git_branch:
                write_git_status_cache(session_id, "branch", git_branch)
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: git branch failed: {e}", file=sys.stderr)
        git_branch = ""

    # --- Collect changed files (with session cache, 2s TTL — changes frequently) ---
    try:
        cached = get_cached_git_status(session_id, "diff", ttl=2)
        if cached is not None:
            changed_files = [f for f in cached.splitlines() if f.strip()][:20]
        else:
            result = subprocess.run(
                ["git", "-C", str(cwd), "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            changed_files = [f for f in result.stdout.splitlines() if f.strip()][:20]
            if result.returncode == 0:
                write_git_status_cache(session_id, "diff", result.stdout)
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
        cache.set("compact-snapshot", snapshot, session_id, ttl=0, invalidation="session")
    except Exception as e:
        print(f"[zf] sdlc-compact: snapshot write failed: {e}", file=sys.stderr)

    # --- Also persist to CLAUDE_PLUGIN_DATA for cross-session survival ---
    try:
        persist_path = persistent_project_path("compact-snapshot", project_name)
        safe_write_persistent(persist_path, json.dumps(snapshot))
    except Exception as e:
        print(f"[zf] sdlc-compact: persistent snapshot write failed: {e}", file=sys.stderr)

elif hook_event_name == "PostCompact":
    # --- Read snapshot; try CacheManager then persistent then live ROADMAP ---
    snapshot = None
    # Try CacheManager session cache first
    try:
        cached_snap = cache.get("compact-snapshot", session_id)
        if cached_snap is not None and isinstance(cached_snap, dict):
            snapshot = cached_snap
    except Exception as e:
        log_error("sdlc-compact", "cache_snapshot_read", e)

    # Fall back to persistent storage
    if snapshot is None:
        for _read_path in (persistent_project_path("compact-snapshot", project_name),):
            try:
                if _read_path.exists():
                    snapshot = json.loads(_read_path.read_text())
                    break
            except (json.JSONDecodeError, OSError) as e:
                log_error("sdlc-compact", "persistent_snapshot_read", e)
                continue
            except Exception as e:
                log_error("sdlc-compact", "persistent_snapshot_read", e)
                continue

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
        lines = []
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

        # --- Sprint active guard: inject SPRINT ACTIVE directive if .sprint-state exists ---
        try:
            sprint_state_path = zf / ".sprint-state"
            if sprint_state_path.exists():
                state = json.loads(sprint_state_path.read_text())
                phase = state.get("phase", "?")
                remaining = state.get("remaining_items", [])
                current_task = state.get("current_task", "")
                tdd = state.get("tdd_phase", "")
                last_action = state.get("last_action", "")
                sprint_line = f"SPRINT ACTIVE — Phase {phase}/4"
                if current_task:
                    sprint_line += f", current task: {current_task}"
                if tdd:
                    sprint_line += f", TDD phase: {tdd}"
                if remaining:
                    sprint_line += f", {len(remaining)} items remaining"
                if last_action:
                    sprint_line += f", last: {last_action}"
                lines.append(sprint_line)
        except Exception as e:
            print(f"[zie-framework] sdlc-compact: sprint-state guard failed: {e}", file=sys.stderr)

        context = "\n".join(lines)
        print(json.dumps({"additionalContext": context}))
    except Exception as e:
        print(f"[zie-framework] sdlc-compact: context build failed: {e}", file=sys.stderr)
        print(json.dumps({"additionalContext": ""}))
