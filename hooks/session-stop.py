#!/usr/bin/env python3
"""Session stop hook — extract patterns and write session memory.

Auto-learn: captures session transcript, extracts patterns (heuristic + optional LLM),
scores confidence, and writes session memory JSON to .zie/memory/session-*.json.

Triggered on Stop event. Runs async (background: true in hooks.json).
Always exits 0 — never blocks Claude.
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path
from utils_roadmap import parse_roadmap_now, SDLC_STAGES
from utils_error import log_error

# Pattern detection thresholds
_MIN_PATTERN_FREQUENCY = 3  # Min occurrences to be a pattern
_HIGH_CONFIDENCE_THRESHOLD = 0.80
_AUTO_APPLY_THRESHOLD = 0.95

# Tool call sequence patterns (regex for common workflows)
_TOOL_SEQUENCES = {
    "tdd_loop": r"(Read|Glob|Grep).*?(Write|Edit).*?(Bash.*?test)",
    "spec_plan_impl": r"(spec|design).*?(plan).*?(implement|code|build)",
    "fix_verify": r"(fix|bug|issue).*?(test|verify|check)",
}

# Category keywords
_CATEGORY_KEYWORDS = {
    "workflow": ["sequence", "loop", "cycle", "pipeline", "stage", "phase", "step"],
    "code": ["naming", "structure", "organization", "pattern", "style", "format"],
    "decision": ["chose", "decided", "selected", "preferred", "option", "trade-off"],
    "communication": ["question", "clarify", "confirm", "approve", "feedback"],
}


def _extract_session_summary(transcript_lines):
    """Generate a 1-2 sentence summary from transcript."""
    # Simple extractive summary: first and last meaningful lines
    meaningful = [l for l in transcript_lines if len(l.strip()) > 20 and not l.strip().startswith("#")]
    if len(meaningful) >= 2:
        return f"{meaningful[0][:100]}... {meaningful[-1][:100]}..."
    elif meaningful:
        return meaningful[0][:200]
    return "Session completed"


def _extract_tool_stats(transcript_lines):
    """Count tool calls from transcript."""
    stats = {
        "tool_calls": 0,
        "files_modified": 0,
        "tests_run": 0,
        "commits": 0,
        "lines_added": 0,
        "lines_deleted": 0,
    }

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
    """Detect pattern category from text content."""
    text_lower = text.lower()
    scores = {}
    for category, keywords in _CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for kw in keywords if kw in text_lower)
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "workflow"  # Default category


def _extract_patterns_heuristic(transcript_lines, tool_stats):
    """Extract patterns using heuristic analysis."""
    patterns = []
    transcript_text = "\n".join(transcript_lines)

    # Detect tool call sequences
    for seq_name, seq_pattern in _TOOL_SEQUENCES.items():
        matches = re.findall(seq_pattern, transcript_text, re.IGNORECASE)
        if len(matches) >= _MIN_PATTERN_FREQUENCY:
            patterns.append({
                "id": f"workflow-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(patterns)+1:03d}",
                "category": "workflow",
                "description": f"Repeated {seq_name.replace('_', ' ')} sequence",
                "frequency": len(matches),
                "evidence": [f"{seq_name} detected {len(matches)} times"],
            })

    # Detect repeated keywords/phrases
    word_freq = {}
    for line in transcript_lines:
        words = re.findall(r'\b\w{4,}\b', line.lower())
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

    for word, freq in word_freq.items():
        if freq >= _MIN_PATTERN_FREQUENCY and word not in {"the", "and", "that", "with", "this"}:
            category = _detect_pattern_category(word)
            patterns.append({
                "id": f"{category}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{len(patterns)+1:03d}",
                "category": category,
                "description": f"Frequent term: {word}",
                "frequency": freq,
                "evidence": [f"'{word}' appeared {freq} times"],
            })

    return patterns


def _score_pattern_confidence(pattern, session_history=None):
    """Calculate confidence score 0.0-1.0 for a pattern."""
    # Frequency component (40%)
    freq_score = min(1.0, pattern.get("frequency", 0) / 10)

    # Consistency component (30%) — simplified: high frequency = high consistency
    consistency_score = min(1.0, freq_score * 1.2)

    # Recency component (30%) — all patterns from this session are fresh
    recency_score = 1.0

    return round(0.4 * freq_score + 0.3 * consistency_score + 0.3 * recency_score, 2)


def _extract_context_keywords(transcript_lines, roadmap_now):
    """Extract top 5 context keywords from session."""
    # Combine transcript with current feature context
    text = " ".join(transcript_lines) + " " + " ".join(roadmap_now or [])

    # Extract meaningful keywords
    words = re.findall(r'\b[a-z]{4,20}\b', text.lower())

    # Filter common words
    stop_words = {"that", "with", "this", "from", "have", "been", "were", "would", "could", "should"}
    filtered = [w for w in words if w not in stop_words]

    # Count frequency
    freq = {}
    for word in filtered:
        freq[word] = freq.get(word, 0) + 1

    # Return top 5
    top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
    return [word for word, _ in top]


def _write_session_memory(session_data, cwd):
    """Write session memory JSON file."""
    # Use project-scoped memory dir under zie-framework/
    zf = cwd / "zie-framework"
    memory_dir = zf / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    timestamp = session_data["timestamp"]["end"].replace("-", "").replace(":", "").replace("T", "-")
    session_file = memory_dir / f"session-{timestamp}.json"

    # Write with secure permissions
    tmp_file = session_file.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(session_data, indent=2))
    os.chmod(tmp_file, 0o600)
    tmp_file.replace(session_file)

    # Update latest symlink
    latest_link = memory_dir / "latest.json"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    try:
        latest_link.symlink_to(session_file.name)
    except OSError:
        pass  # Symlinks may not be supported on all filesystems


def _detect_sdlc_stage(roadmap_now):
    """Detect current SDLC stage from ROADMAP Now lane."""
    if not roadmap_now:
        return "idle"

    now_text = " ".join(roadmap_now).lower()

    for stage in SDLC_STAGES:
        if stage in now_text:
            return stage

    return "in-progress"


# Main execution
try:
    event = read_event()
    cwd = get_cwd()
    zf = cwd / "zie-framework"

    if not zf.exists():
        sys.exit(0)

    project = cwd.name

    # Get session metadata
    session_id = os.environ.get("CLAUDE_SESSION_ID", datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))

    # Read ROADMAP for context
    roadmap_file = zf / "ROADMAP.md"
    now_lines = parse_roadmap_now(roadmap_file) if roadmap_file.exists() else []

    # Extract transcript from event (if available)
    transcript_lines = []
    if event and "conversation_history" in event:
        transcript_lines = event.get("conversation_history", [])
    elif event and "messages" in event:
        transcript_lines = event.get("messages", [])

    # Build session memory
    end_time = datetime.now(timezone.utc)
    session_data = {
        "session_id": session_id,
        "timestamp": {
            "start": end_time.isoformat(),  # Would be more accurate with session start tracking
            "end": end_time.isoformat(),
        },
        "summary": _extract_session_summary(transcript_lines),
        "statistics": _extract_tool_stats(transcript_lines),
        "patterns": [],
        "decisions": [],
        "context_keywords": _extract_context_keywords(transcript_lines, now_lines),
        "active_feature": now_lines[0][:50] if now_lines else None,
        "sdlc_stage": _detect_sdlc_stage(now_lines),
    }

    # Extract patterns
    patterns = _extract_patterns_heuristic(transcript_lines, session_data["statistics"])

    # Score patterns and add metadata
    for pattern in patterns:
        confidence = _score_pattern_confidence(pattern)
        pattern["confidence"] = confidence
        pattern["auto_apply"] = confidence >= _AUTO_APPLY_THRESHOLD
        session_data["patterns"].append(pattern)

    # Write session memory
    _write_session_memory(session_data, cwd)

    # Write pending_learn marker for next session (integration with session-learn.py)
    pending_learn_file = zf / "pending_learn.txt"
    wip_context = "; ".join(now_lines[:3]) if now_lines else ""
    try:
        pending_learn_file.write_text(f"project={project}\nwip={wip_context}\n")
        os.chmod(pending_learn_file, 0o600)
    except (OSError, PermissionError) as e:
        log_error("session-stop", "write_pending_learn", e)

    sys.exit(0)

except Exception as e:
    # Never block Claude on hook failure
    print(f"[zie-framework] session-stop: {e}", file=sys.stderr)
    sys.exit(0)
