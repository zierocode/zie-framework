#!/usr/bin/env python3
"""Stop hook — store session learnings in zie-memory and write pending_learn."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import call_zie_memory_api, get_cwd, read_event
from utils_io import atomic_write, persistent_project_path, project_tmp_path
from utils_roadmap import parse_roadmap_now

_STAGE_KEYWORDS = [
    ("spec",      ["spec"]),
    ("plan",      ["plan"]),
    ("implement", ["implement", "code", "build"]),
    ("fix",       ["fix", "bug"]),
    ("release",   ["release", "deploy"]),
    ("retro",     ["retro"]),
]

_PATTERN_LOG_LINES_TRIGGER = 10  # rebuild aggregate every N sessions
_PATTERN_LOG_LOOKBACK = 30       # use last N records for aggregate


def _detect_stage(task_text: str) -> str:
    """Derive SDLC stage from a ROADMAP task label."""
    lower = task_text.lower()
    for stage, keywords in _STAGE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return stage
    return "in-progress"


def _rebuild_aggregate(log_path: Path, agg_path: Path) -> None:
    """Rebuild pattern aggregate from the last N log records."""
    lines = log_path.read_text().strip().splitlines()
    records = []
    for line in lines[-_PATTERN_LOG_LOOKBACK:]:
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    if not records:
        return
    stage_counts: dict = {}
    for r in records:
        s = r.get("stage", "idle")
        stage_counts[s] = stage_counts.get(s, 0) + 1
    aggregate = {
        "session_count": len(lines),
        "most_common_stage": max(stage_counts, key=stage_counts.get),
        "stage_counts": stage_counts,
        "rebuilt_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    tmp_path_obj = Path(str(agg_path) + ".tmp")
    tmp_path_obj.write_text(json.dumps(aggregate))
    os.chmod(tmp_path_obj, 0o600)
    tmp_path_obj.replace(agg_path)


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
    now_lines = parse_roadmap_now(roadmap_file)
    wip_context = "; ".join(now_lines[:3]) if now_lines else ""
    stage_at_end = _detect_stage(now_lines[0]) if now_lines else "idle"

    atomic_write(
        pending_learn_file,
        f"project={project}\n"
        f"wip={wip_context}\n",
    )

    # ── Adaptive learning: record session pattern ────────────────────────────
    _log_path = project_tmp_path("pattern-log", project)
    _agg_path = project_tmp_path("pattern-aggregate", project)
    try:
        _record = json.dumps({
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stage": stage_at_end,
            "wip": wip_context[:120],
        })
        with open(_log_path, "a") as _f:
            _f.write(_record + "\n")
        os.chmod(_log_path, 0o600)
        # Rebuild aggregate every N sessions
        _line_count = sum(1 for _ in open(_log_path))
        if _line_count >= _PATTERN_LOG_LINES_TRIGGER and _line_count % _PATTERN_LOG_LINES_TRIGGER == 0:
            _rebuild_aggregate(_log_path, _agg_path)
    except Exception:
        pass  # never block on pattern log write failure

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
