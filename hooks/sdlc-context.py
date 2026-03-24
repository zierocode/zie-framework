#!/usr/bin/env python3
"""UserPromptSubmit hook — inject current SDLC state as additionalContext."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import parse_roadmap_now, project_tmp_path, read_event, get_cwd

# ── Stage keyword map (checked in order; first match wins) ──────────────────

STAGE_KEYWORDS = [
    ("spec",      ["spec"]),
    ("plan",      ["plan"]),
    ("implement", ["implement", "code", "build"]),
    ("fix",       ["fix", "bug"]),
    ("release",   ["release", "deploy"]),
    ("retro",     ["retro"]),
]

# ── Stage → suggested /zie-* command ────────────────────────────────────────

STAGE_COMMANDS = {
    "spec":        "/zie-spec",
    "plan":        "/zie-plan",
    "implement":   "/zie-implement",
    "fix":         "/zie-fix",
    "release":     "/zie-release",
    "retro":       "/zie-retro",
    "in-progress": "/zie-status",
    "idle":        "/zie-status",
}

STALE_THRESHOLD_SECS = 300


def derive_stage(task_text: str) -> str:
    """Return SDLC stage name by matching task_text against STAGE_KEYWORDS.

    Only the part before the em-dash separator (used for plan links) is used
    for detection, so '— plan' suffixes from ROADMAP links don't skew the stage.
    """
    main = task_text.split("—")[0].strip()
    lower = main.lower()
    for stage, keywords in STAGE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return stage
    return "in-progress"


def get_test_status(cwd: Path) -> str:
    """Return 'recent', 'stale', or 'unknown' based on last-test tmp file mtime."""
    tmp_file = project_tmp_path("last-test", cwd.name)
    try:
        mtime = tmp_file.stat().st_mtime
        age = time.time() - mtime
        return "stale" if age > STALE_THRESHOLD_SECS else "recent"
    except Exception:
        return "unknown"


# ── Outer guard ──────────────────────────────────────────────────────────────
try:
    event = read_event()
except SystemExit:
    sys.exit(0)

try:
    cwd = get_cwd()

    if not (cwd / "zie-framework").exists():
        sys.exit(0)

    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
    now_items = parse_roadmap_now(roadmap_path)

    if now_items:
        raw_task = now_items[0]
        active_task = raw_task[:80]
        stage = derive_stage(active_task)
    else:
        active_task = "none"
        stage = "idle"

    suggested_cmd = STAGE_COMMANDS.get(stage, "/zie-status")
    test_status = get_test_status(cwd)

    context = (
        f"[sdlc] task: {active_task} | "
        f"stage: {stage} | "
        f"next: {suggested_cmd} | "
        f"tests: {test_status}"
    )

    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"},
        "additionalContext": context,
    }))

except Exception as e:
    print(f"[zie-framework] sdlc-context: {e}", file=sys.stderr)
    sys.exit(0)
