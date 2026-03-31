#!/usr/bin/env python3
"""UserPromptSubmit hook — detect SDLC intent and inject current SDLC state.

Merged replacement for intent-detect.py + sdlc-context.py.
Reads ROADMAP.md once (via session cache) and produces a single
additionalContext payload combining intent suggestion + SDLC state.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    get_cwd,
    parse_roadmap_section_content,
    project_tmp_path,
    read_event,
    read_roadmap_cached,
)

# ── Intent detection constants ────────────────────────────────────────────────

MAX_MESSAGE_LEN = 1000

PATTERNS = {
    "init": [
        r"\binit\b", r"เริ่มต้น.*project", r"ตั้งค่า.*project",
        r"setup.*project", r"bootstrap",
    ],
    "backlog": [
        r"อยากทำ", r"อยากได้", r"อยากเพิ่ม", r"อยากสร้าง",
        r"\bidea\b", r"\bfeature\b", r"new feature", r"เพิ่ม.*feature",
        r"สร้าง.*ใหม่", r"want to (build|add|create|make)",
        r"ต้องการ", r"would like to", r"\bbacklog\b", r"capture.*idea",
    ],
    "spec": [
        r"\bspec\b", r"design.*doc", r"write.*spec", r"spec.*feature",
        r"เขียน.*spec", r"ออกแบบ", r"design.*feature",
    ],
    "plan": [
        r"\bplan\b", r"วางแผน", r"อยากวางแผน", r"เลือก.*backlog",
        r"หยิบ.*backlog", r"plan.*feature", r"ready.*to.*plan",
        r"zie.?plan",
    ],
    "implement": [
        r"implement", r"ทำ.*ต่อ", r"continue", r"resume",
        r"สร้าง.*feature", r"next task", r"task.*ต่อ",
        r"code.*this", r"let.*s.*build", r"start.*coding",
    ],
    "fix": [
        r"\bbug\b", r"พัง", r"\berror\b", r"\bfix\b",
        r"ไม่ทำงาน", r"\bcrash\b", r"exception", r"traceback",
        r"ล้มเหลว", r"broken", r"doesn.*t work", r"not working",
        r"failed", r"failure",
    ],
    "release": [
        r"\brelease\b", r"\bdeploy\b", r"\bpublish\b",
        r"merge.*main", r"go.*live", r"launch", r"ready.*to.*release",
        r"ปล่อย", r"deploy.*now",
    ],
    "retro": [
        r"\bretro\b", r"retrospective", r"สรุป.*session", r"ทบทวน",
        r"review.*session", r"what.*did.*we", r"what.*we.*learned",
        r"what.*worked",
    ],
    "sprint": [
        r"\bsprint\b", r"zie.?sprint",
        r"clear.*backlog", r"เคลียร์.*backlog",
        r"ship.*all", r"ทำ.*ทั้งหมด",
        r"batch.*release", r"full.*pipeline",
    ],
    "status": [
        r"\bstatus\b", r"ทำอะไรอยู่", r"where.*am.*i", r"progress",
        r"what.*next", r"ต่อไปทำ", r"ถัดไป", r"สถานะ",
    ],
}

COMPILED_PATTERNS = {
    cat: [re.compile(p) for p in pats]
    for cat, pats in PATTERNS.items()
}

SUGGESTIONS = {
    "init":      "/zie-init",
    "backlog":   "/zie-backlog",
    "spec":      "/zie-spec",
    "plan":      "/zie-plan",
    "implement": "/zie-implement",
    "fix":       "/zie-fix",
    "release":   "/zie-release",
    "retro":     "/zie-retro",
    "sprint":    "/zie-sprint",
    "status":    "/zie-status",
}

# ── SDLC context constants ────────────────────────────────────────────────────

STAGE_KEYWORDS = [
    ("spec",      ["spec"]),
    ("plan",      ["plan"]),
    ("implement", ["implement", "code", "build"]),
    ("fix",       ["fix", "bug"]),
    ("release",   ["release", "deploy"]),
    ("retro",     ["retro"]),
]

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


def _extract_roadmap_slugs(roadmap_content: str) -> list:
    """Return deduplicated kebab-case slugs from Next and Ready lane items."""
    slugs = []
    in_target = False
    for line in roadmap_content.splitlines():
        if line.startswith("##") and any(
            s in line.lower() for s in ("next", "ready")
        ):
            in_target = True
            continue
        if line.startswith("##") and in_target:
            in_target = False
            continue
        if in_target and line.strip().startswith("- "):
            tokens = re.findall(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)+', line.lower())
            slugs.extend(tokens)
    return list(dict.fromkeys(slugs))


def _spec_approved(cwd: Path, slug: str) -> bool:
    """Return True if zie-framework/specs/*-<slug>-design.md has approved: true."""
    specs_dir = cwd / "zie-framework" / "specs"
    try:
        matches = list(specs_dir.glob(f"*-{slug}-design.md"))
    except Exception:
        return False
    if not matches:
        return False
    try:
        content = matches[0].read_text()
        return bool(re.search(r'^approved:\s*true\s*$', content, re.MULTILINE))
    except Exception:
        return False


def _check_pipeline_preconditions(
    intent: str, roadmap_content: str, cwd: Path, message: str
) -> "str | None":
    """Return a directive block if preconditions fail, else None."""
    if intent == "plan":
        slugs = _extract_roadmap_slugs(roadmap_content)
        matched = [s for s in slugs if s in message]
        if not matched:
            return None
        blocking = [s for s in matched if not _spec_approved(cwd, s)]
        if not blocking:
            return None
        slug_list = ", ".join(f"'{s}'" for s in blocking)
        return (
            f"⛔ STOP. No approved spec for {slug_list}. "
            f"You must run /zie-spec {blocking[0]} first. "
            f"Do not proceed with planning."
        )

    if intent == "implement":
        in_now = False
        for line in roadmap_content.splitlines():
            if line.startswith("##") and "now" in line.lower():
                in_now = True
                continue
            if line.startswith("##") and in_now:
                break
            if in_now and re.search(r'-\s*\[\s*\]', line):
                return None  # has open item — gate passes
        return (
            "⛔ STOP. No active feature in Now lane. "
            "Complete /zie-backlog → /zie-spec → /zie-plan first, "
            "then start /zie-implement. Do not write code."
        )

    return None


def _positional_guidance(roadmap_content: str, cwd: Path, message: str) -> "str | None":
    """Return stage-aware nudge for a known ROADMAP slug when no gate fired."""
    slugs = _extract_roadmap_slugs(roadmap_content)
    matched = [s for s in slugs if s in message]
    if not matched:
        return None
    slug = matched[0]
    has_approved_spec = _spec_approved(cwd, slug)
    slug_in_ready = False
    in_ready_section = False
    for line in roadmap_content.splitlines():
        if line.startswith("##") and "ready" in line.lower():
            in_ready_section = True
            continue
        if line.startswith("##") and in_ready_section:
            break
        if in_ready_section and slug in line.lower():
            slug_in_ready = True
            break
    if not has_approved_spec:
        return f"Feature '{slug}' is in backlog. Start with /zie-spec {slug}"
    if has_approved_spec and not slug_in_ready:
        return f"Spec approved for '{slug}'. Run /zie-plan {slug}"
    return f"Plan ready for '{slug}'. Run /zie-implement to start"


def derive_stage(task_text: str) -> str:
    main = task_text.split("—")[0].strip()
    lower = main.lower()
    for stage, keywords in STAGE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return stage
    return "in-progress"


def get_test_status(cwd: Path) -> str:
    tmp_file = project_tmp_path("last-test", cwd.name)
    try:
        mtime = tmp_file.stat().st_mtime
        age = time.time() - mtime
        return "stale" if age > STALE_THRESHOLD_SECS else "recent"
    except Exception:
        return "unknown"


# ── Outer guard ───────────────────────────────────────────────────────────────

try:
    event = read_event()
except Exception:
    sys.exit(0)

try:
    message = (event.get("prompt") or "").lower().strip()

    if not message or len(message) < 3:
        sys.exit(0)
    if len(message) > MAX_MESSAGE_LEN:
        sys.exit(0)
    if message.startswith("---") or len(message) > 500:
        sys.exit(0)
    if message.startswith("/zie-"):
        sys.exit(0)

    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Inner operations ──────────────────────────────────────────────────────────

try:
    session_id = event.get("session_id", "default")

    # ── Intent detection (no ROADMAP needed) ─────────────────────────────────
    intent_cmd = None
    best = None
    scores = {}
    for category, compiled_pats in COMPILED_PATTERNS.items():
        score = sum(1 for p in compiled_pats if p.search(message))
        if score > 0:
            scores[category] = score

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] >= 1:
            if best == "init" and (cwd / "zie-framework" / ".config").exists():
                pass  # already initialized — suppress init suggestion
            else:
                intent_cmd = SUGGESTIONS[best]

    # ── SDLC context (reads ROADMAP once via cache) ───────────────────────────
    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
    roadmap_content = read_roadmap_cached(roadmap_path, session_id)
    now_items = parse_roadmap_section_content(roadmap_content, "now")

    if now_items:
        raw_task = now_items[0]
        active_task = raw_task[:80]
        stage = derive_stage(active_task)
    else:
        active_task = "none"
        stage = "idle"

    suggested_cmd = STAGE_COMMANDS.get(stage, "/zie-status")
    test_status = get_test_status(cwd)

    # ── Pipeline gate check ───────────────────────────────────────────────────
    gate_msg = None
    if best and best in ("plan", "implement"):
        gate_msg = _check_pipeline_preconditions(best, roadmap_content, cwd, message)

    # ── Positional guidance (only when no gate and no dominant intent) ────────
    guidance_msg = None
    if gate_msg is None and not intent_cmd:
        guidance_msg = _positional_guidance(roadmap_content, cwd, message)

    # ── Build combined context ────────────────────────────────────────────────
    parts = []
    if gate_msg:
        parts.append(gate_msg)
    elif intent_cmd:
        parts.append(f"intent:{best} → {intent_cmd}")
    if guidance_msg:
        parts.append(guidance_msg)
    parts.append(
        f"task:{active_task} | stage:{stage} | next:{suggested_cmd} | tests:{test_status}"
    )
    context = "[zie-framework] " + " | ".join(parts)

    print(json.dumps({"additionalContext": context}))

except Exception as e:
    print(f"[zie-framework] intent-sdlc: {e}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    pass
