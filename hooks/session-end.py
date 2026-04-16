#!/usr/bin/env python3
"""Unified Stop hook — merges session-stop, session-learn, session-cleanup.

Runs three phases on session end:
1. Pattern extraction + session memory write (from session-stop)
2. Learning record + pattern aggregate rebuild (from session-learn)
3. Cache/session cleanup + /tmp file removal (from session-cleanup)

Always exits 0 — never blocks Claude.
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_cache import get_cache_manager
from utils_error import log_error
from utils_event import call_zie_memory_api, get_cwd, read_event
from utils_io import atomic_write, project_tmp_path, safe_project_name
from utils_roadmap import SDLC_STAGES, parse_roadmap_now

# ── Phase 1 constants (from session-stop) ──────────────────────────────────────
_MIN_PATTERN_FREQUENCY = 3
_HIGH_CONFIDENCE_THRESHOLD = 0.80
_AUTO_APPLY_THRESHOLD = 0.95

_TOOL_SEQUENCES = {
    "tdd_loop": r"(Read|Glob|Grep).*?(Write|Edit).*?(Bash.*?test)",
    "spec_plan_impl": r"(spec|design).*?(plan).*?(implement|code|build)",
    "fix_verify": r"(fix|bug|issue).*?(test|verify|check)",
}

_CATEGORY_KEYWORDS = {
    "workflow": ["sequence", "loop", "cycle", "pipeline", "stage", "phase", "step"],
    "code": ["naming", "structure", "organization", "pattern", "style", "format"],
    "decision": ["chose", "decided", "selected", "preferred", "option", "trade-off"],
    "communication": ["question", "clarify", "confirm", "approve", "feedback"],
}

# ── Phase 2 constants (from session-learn) ─────────────────────────────────────
_STAGE_KEYWORDS = [
    ("spec", ["spec"]),
    ("plan", ["plan"]),
    ("implement", ["implement", "code", "build"]),
    ("fix", ["fix", "bug"]),
    ("release", ["release", "deploy"]),
    ("retro", ["retro"]),
]

_PATTERN_LOG_LINES_TRIGGER = 10
_PATTERN_LOG_LOOKBACK = 30


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 1: Pattern extraction + session memory (from session-stop)
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_session_summary(transcript_lines):
    meaningful = [line for line in transcript_lines if len(line.strip()) > 20 and not line.strip().startswith("#")]
    if len(meaningful) >= 2:
        return f"{meaningful[0][:100]}... {meaningful[-1][:100]}..."
    elif meaningful:
        return meaningful[0][:200]
    return "Session completed"


def _extract_tool_stats(transcript_lines):
    stats = {"tool_calls": 0, "files_modified": 0, "tests_run": 0, "commits": 0}
    tool_pattern = re.compile(r"Called the (\w+) tool")
    for line in transcript_lines:
        if tool_pattern.search(line):
            stats["tool_calls"] += 1
        if "Write" in line or "Edit" in line:
            stats["files_modified"] += 1
        if "test" in line.lower() and ("run" in line.lower() or "pytest" in line.lower()):
            stats["tests_run"] += 1
        if "git commit" in line.lower():
            stats["commits"] += 1
    return stats


def _detect_pattern_category(text):
    text_lower = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in text_lower) for cat, kws in _CATEGORY_KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "workflow"


def _extract_patterns_heuristic(transcript_lines, tool_stats):
    patterns = []
    transcript_text = "\n".join(transcript_lines)
    for seq_name, seq_pattern in _TOOL_SEQUENCES.items():
        matches = re.findall(seq_pattern, transcript_text, re.IGNORECASE)
        if len(matches) >= _MIN_PATTERN_FREQUENCY:
            patterns.append({
                "id": f"workflow-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(patterns) + 1:03d}",
                "category": "workflow",
                "description": f"Repeated {seq_name.replace('_', ' ')} sequence",
                "frequency": len(matches),
                "evidence": [f"{seq_name} detected {len(matches)} times"],
            })
    word_freq = {}
    for line in transcript_lines:
        for word in re.findall(r"\b\w{4,}\b", line.lower()):
            word_freq[word] = word_freq.get(word, 0) + 1
    for word, freq in word_freq.items():
        if freq >= _MIN_PATTERN_FREQUENCY and word not in {"the", "and", "that", "with", "this"}:
            cat = _detect_pattern_category(word)
            patterns.append({
                "id": f"{cat}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(patterns) + 1:03d}",
                "category": cat, "description": f"Frequent term: {word}",
                "frequency": freq, "evidence": [f"'{word}' appeared {freq} times"],
            })
    return patterns


def _score_pattern_confidence(pattern):
    freq_score = min(1.0, pattern.get("frequency", 0) / 10)
    consistency_score = min(1.0, freq_score * 1.2)
    recency_score = 1.0
    return round(0.4 * freq_score + 0.3 * consistency_score + 0.3 * recency_score, 2)


def _extract_context_keywords(transcript_lines, roadmap_now):
    text = " ".join(transcript_lines) + " " + " ".join(roadmap_now or [])
    words = re.findall(r"\b[a-z]{4,20}\b", text.lower())
    stop_words = {"that", "with", "this", "from", "have", "been", "were", "would", "could", "should"}
    filtered = [w for w in words if w not in stop_words]
    freq = {}
    for word in filtered:
        freq[word] = freq.get(word, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]


def _write_session_memory(session_data, cwd):
    zf = cwd / "zie-framework"
    memory_dir = zf / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    timestamp = session_data["timestamp"]["end"].replace("-", "").replace(":", "").replace("T", "-")
    session_file = memory_dir / f"session-{timestamp}.json"
    tmp_file = session_file.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(session_data, indent=2))
    os.chmod(tmp_file, 0o600)
    tmp_file.replace(session_file)
    latest_link = memory_dir / "latest.json"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    try:
        latest_link.symlink_to(session_file.name)
        if latest_link.is_symlink():
            resolved = latest_link.resolve()
            if not str(resolved).startswith(str(memory_dir.resolve())):
                latest_link.unlink()
    except OSError:
        pass


def _detect_sdlc_stage(roadmap_now):
    if not roadmap_now:
        return "idle"
    now_text = " ".join(roadmap_now).lower()
    for stage in SDLC_STAGES:
        if stage in now_text:
            return stage
    return "in-progress"


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 2: Learning + pattern aggregate (from session-learn)
# ═══════════════════════════════════════════════════════════════════════════════

def _detect_stage(task_text):
    lower = task_text.lower()
    for stage, keywords in _STAGE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return stage
    return "in-progress"


def _rebuild_aggregate(log_path, agg_path):
    lines = log_path.read_text().strip().splitlines()
    records = []
    for line in lines[-_PATTERN_LOG_LOOKBACK:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    if not records:
        return
    stage_counts = {}
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


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: Cache cleanup + /tmp file removal (from session-cleanup)
# ═══════════════════════════════════════════════════════════════════════════════

def _cleanup_session(event, cwd):
    session_id = event.get("session_id", "")
    safe_project = safe_project_name(cwd.name)

    # CacheManager session cleanup
    if session_id:
        try:
            cache = get_cache_manager(cwd)
            cache.clear_session(session_id)
        except Exception as e:
            print(f"[zf] session-end/cleanup: cache clear failed: {e}", file=sys.stderr)

    # Remove project-scoped /tmp files (preserve pattern-log and pattern-aggregate)
    _PRESERVE_SUFFIXES = ("pattern-log", "pattern-aggregate")
    for tmp_file in Path(tempfile.gettempdir()).glob(f"zie-{safe_project}-*"):
        if any(tmp_file.name.endswith(s) for s in _PRESERVE_SUFFIXES):
            continue
        try:
            tmp_file.unlink()
        except Exception as e:
            print(f"[zf] session-end/cleanup: {e}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════════
# Main execution
# ═══════════════════════════════════════════════════════════════════════════════

try:
    event = read_event()
except (json.JSONDecodeError, OSError):
    sys.exit(0)

try:
    cwd = get_cwd()
    zf = cwd / "zie-framework"

    if not zf.exists():
        sys.exit(0)

    project = cwd.name
    session_id = os.environ.get("CLAUDE_SESSION_ID", datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))

    # ── Phase 1: Session memory (session-stop) ──────────────────────────────
    roadmap_file = zf / "ROADMAP.md"
    now_lines = parse_roadmap_now(roadmap_file) if roadmap_file.exists() else []

    transcript_lines = []
    if event and "conversation_history" in event:
        transcript_lines = event.get("conversation_history", [])
    elif event and "messages" in event:
        transcript_lines = event.get("messages", [])

    end_time = datetime.now(timezone.utc)
    session_data = {
        "session_id": session_id,
        "timestamp": {"start": end_time.isoformat(), "end": end_time.isoformat()},
        "summary": _extract_session_summary(transcript_lines),
        "statistics": _extract_tool_stats(transcript_lines),
        "patterns": [],
        "decisions": [],
        "context_keywords": _extract_context_keywords(transcript_lines, now_lines),
        "active_feature": now_lines[0][:50] if now_lines else None,
        "sdlc_stage": _detect_sdlc_stage(now_lines),
    }

    patterns = _extract_patterns_heuristic(transcript_lines, session_data["statistics"])
    for pattern in patterns:
        pattern["confidence"] = _score_pattern_confidence(pattern)
        pattern["auto_apply"] = pattern["confidence"] >= _AUTO_APPLY_THRESHOLD
        session_data["patterns"].append(pattern)

    _write_session_memory(session_data, cwd)

    # Write pending_learn marker
    pending_learn_file = zf / "pending_learn.txt"
    wip_context = "; ".join(now_lines[:3]) if now_lines else ""
    try:
        pending_learn_file.write_text(f"project={project}\nwip={wip_context}\n")
        os.chmod(pending_learn_file, 0o600)
    except (OSError, PermissionError) as e:
        log_error("session-end", "write_pending_learn", e)

    # ── Phase 2: Learning + pattern aggregate (session-learn) ────────────────
    stage_at_end = _detect_stage(now_lines[0]) if now_lines else "idle"

    try:
        atomic_write(pending_learn_file, f"project={project}\nwip={wip_context}\n")
        os.chmod(pending_learn_file, 0o600)
    except (OSError, PermissionError) as e:
        log_error("session-end", "write_pending_learn_phase2", e)

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
        _line_count = sum(1 for _ in open(_log_path))
        if _line_count >= _PATTERN_LOG_LINES_TRIGGER and _line_count % _PATTERN_LOG_LINES_TRIGGER == 0:
            _rebuild_aggregate(_log_path, _agg_path)
    except Exception as e:
        log_error("session-end", "pattern_log_write", e)

    # Fast-path: honour ZIE_MEMORY_ENABLED=0 injected by session-resume.py
    _mem_enabled = os.environ.get("ZIE_MEMORY_ENABLED", "").strip()
    if _mem_enabled != "0":
        api_key = os.environ.get("ZIE_MEMORY_API_KEY", "")
        api_url = os.environ.get("ZIE_MEMORY_API_URL", "")
        if api_key and api_url.startswith("https://"):
            try:
                call_zie_memory_api(api_url, api_key, "/api/hooks/session-stop", {
                    "project": project, "wip_summary": wip_context,
                })
            except Exception as e:
                print(f"[zie-framework] session-end/memory: {e}", file=sys.stderr)

    # ── Phase 3: Cache cleanup + /tmp removal (session-cleanup) ──────────────
    _cleanup_session(event, cwd)

except Exception as e:
    print(f"[zie-framework] session-end: {e}", file=sys.stderr)
    sys.exit(0)