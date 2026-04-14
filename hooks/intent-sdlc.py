#!/usr/bin/env python3
"""UserPromptSubmit hook — detect SDLC intent and inject current SDLC state.

Merged replacement for intent-detect.py + sdlc-context.py.
Reads ROADMAP.md once (via session cache) and produces a single
additionalContext payload combining intent suggestion + SDLC state.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path
from utils_config import CACHE_TTLS
from utils_cache import get_cache_manager
from utils_roadmap import is_track_active, parse_roadmap_section_content

# ── Intent detection constants ────────────────────────────────────────────────
# Single combined regex with named groups for one-pass intent detection.
# Each group name is the intent category; match extracts intent directly.

INTENT_PATTERN = re.compile(r"""
    (?P<init>
        \binit\b | เริ่มต้น.*project | ตั้งค่า.*project | setup.*project | bootstrap
    )
    |
    (?P<backlog>
        อยากทำ | อยากได้ | อยากเพิ่ม | อยากสร้าง | \bidea\b | \bfeature\b |
        new\ feature | เพิ่ม.*feature | สร้าง.*ใหม่ |
        want\ to\ (build|add|create|make) | ต้องการ | would\ like\ to |
        \bbacklog\b | capture.*idea
    )
    |
    (?P<spec>
        \bspec\b | design.*doc | write.*spec | spec.*feature |
        เขียน.*spec | ออกแบบ | design.*feature
    )
    |
    (?P<plan>
        \bplan\b | วางแผน | อยากวางแผน | เลือก.*backlog |
        หยิบ.*backlog | plan.*feature | ready.*to.*plan | zie.?plan
    )
    |
    (?P<implement>
        implement | ทำ.*ต่อ | continue | resume | สร้าง.*feature |
        next\ task | task.*ต่อ | code.*this | let.*s.*build | start.*coding
    )
    |
    (?P<fix>
        \bbug\b | พัง | \berror\b | \bfix\b | ไม่ทำงาน | \bcrash\b |
        exception | traceback | ล้มเหลว | broken | doesn.*t\ work |
        not\ working | failed | failure
    )
    |
    (?P<release>
        \brelease\b | \bdeploy\b | \bpublish\b | merge.*main |
        go.*live | launch | ready.*to.*release | ปล่อย | deploy.*now
    )
    |
    (?P<retro>
        \bretro\b | retrospective | สรุป.*session | ทบทวน |
        review.*session | what.*did.*we | what.*we.*learned | what.*worked
    )
    |
    (?P<sprint>
        \bsprint\b | zie.?sprint | clear.*backlog | เคลียร์.*backlog |
        ship.*all | ทำ.*ทั้งหมด | batch.*release | full.*pipeline
    )
    |
    (?P<status>
        \bstatus\b | ทำอะไรอยู่ | where.*am.*i | progress |
        what.*next | ต่อไปทำ | ถัดไป | สถานะ
    )
    |
    (?P<hotfix>
        \bhotfix\b | emergency | prod.*down | urgent.*fix |
        critical.*fix | cannot\ wait | on.*fire | production.*issue
    )
    |
    (?P<chore>
        \bchore\b | bump.*version | update.*docs | housekeeping |
        maintenance | cleanup | tidy.*up
    )
    |
    (?P<spike>
        \bspike\b | \bexplore\b | \binvestigate\b | \bresearch\b |
        \bprototype\b | proof.*of.*concept | \bpoc\b | time.?box
    )
    |
    (?P<brainstorm>
        \bimprove\b | what\ if | \bresearch\b | deep\ dive |
        อยากให้มี | ควรจะ | น่าจะเพิ่ม | ปรับอะไรดี |
        คิดว่าขาดอะไร | \bexplore\b
    )
""", re.IGNORECASE | re.VERBOSE)

# Suggestion mapping for intent → command
SUGGESTIONS = {
    "init":      "/init",
    "backlog":   "/backlog",
    "spec":      "/spec",
    "plan":      "/plan",
    "implement": "/implement",
    "fix":       "/fix",
    "release":   "/release",
    "retro":     "/retro",
    "sprint":    "/sprint",
    "status":    "/status",
    "hotfix":    "/hotfix",
    "chore":     "/chore",
    "spike":     "/spike",
    "brainstorm": "invoke zie-framework:brainstorm skill",
}

# Pre-compiled new-intent signals for sprint/fix/chore detection
NEW_INTENT_REGEXES = {
    "sprint": [re.compile(p, re.IGNORECASE) for p in [
        r"ทำเลย", r"\bimplement\b", r"\bbuild\b", r"สร้าง",
        r"เพิ่ม.*feature", r"start.*coding",
    ]],
    "fix": [re.compile(p, re.IGNORECASE) for p in [
        r"\bbug\b", r"\bbroken\b", r"\berror\b", r"ไม่.*work",
        r"\bcrash\b", r"\bfail\b", r"แก้",
    ]],
    "chore": [re.compile(p, re.IGNORECASE) for p in [
        r"\bupdate\b", r"\bbump\b", r"\brename\b", r"\bcleanup\b",
        r"\brefactor\b", r"ลบ",
    ]],
}
NEW_INTENT_HINTS = {
    "sprint": "confirm backlog→spec→plan before implementing",
    "fix":    "invoke /fix or /hotfix track",
    "chore":  "use /chore to track this maintenance task",
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
    "spec":        "/spec",
    "plan":        "/plan",
    "implement":   "/implement",
    "fix":         "/fix",
    "release":     "/release",
    "retro":       "/retro",
    "in-progress": "/status",
    "idle":        "/status",
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
            f"You must run /spec {blocking[0]} first. "
            f"Do not proceed with planning."
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
        return f"Feature '{slug}' is in backlog. Start with /spec {slug}"
    if has_approved_spec and not slug_in_ready:
        return f"Spec approved for '{slug}'. Run /plan {slug}"
    return f"Plan ready for '{slug}'. Run /implement to start"


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


_DEDUP_TTL_SECS = 600  # 10-minute session window


def _dedup_path(session_id: str, cwd: Path) -> Path:
    """Return the per-session dedup cache file path.

    Includes a short hash of the full cwd path so that different directories
    with the same basename (e.g., pytest tmp dirs across test runs) don't share
    a dedup file.
    """
    safe_sid = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
    cwd_hash = hashlib.md5(str(cwd).encode(), usedforsecurity=False).hexdigest()[:8]
    return project_tmp_path(f"intent-dedup-{safe_sid}-{cwd_hash}", cwd.name)


def _read_dedup(path: Path) -> str:
    """Return last emitted context string, or '' on miss/expired/error."""
    try:
        if time.time() - path.stat().st_mtime > _DEDUP_TTL_SECS:
            return ""  # expired — re-emit after TTL
        return path.read_text()
    except Exception:
        return ""


def _write_dedup(path: Path, context: str) -> None:
    """Write current context to dedup cache (best-effort, never blocks)."""
    try:
        path.write_text(context)
    except Exception:
        pass


# ── Outer guard ───────────────────────────────────────────────────────────────

try:
    event = read_event()
except Exception:
    sys.exit(0)

try:
    message = (event.get("prompt") or "").lower().strip()

    if not message or len(message) < 3:
        sys.exit(0)
    if message.startswith("---") or len(message) > 500:
        sys.exit(0)
    if message.split()[0].startswith("/"):
        sys.exit(0)

    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Inner operations ──────────────────────────────────────────────────────────

try:
    session_id = event.get("session_id", "default")

    # ── Early-exit guard (short + zero SDLC keywords → unclear intent) ─────────
    # Single-pass regex match for all 13 intent categories
    intent_match = INTENT_PATTERN.search(message)
    has_sdlc_keyword = intent_match is not None

    if len(message) < 15:
        if not has_sdlc_keyword:
            context = (
                "[zie-framework] intent: unclear — "
                "please clarify your request before proceeding"
            )
            if session_id != "default":
                _dp = _dedup_path(session_id, cwd)
                if _read_dedup(_dp) == context:
                    sys.exit(0)
                _write_dedup(_dp, context)
            print(json.dumps({"additionalContext": context}))
        sys.exit(0)  # short messages always exit (ambiguous even with keyword)

    if not has_sdlc_keyword:
        sys.exit(0)

    # ── New-intent signal tables (≥2 threshold, evaluated after roadmap read) ──
    NEW_INTENT_HINTS = {
        "sprint": "confirm backlog→spec→plan before implementing",
        "fix":    "invoke /fix or /hotfix track",
        "chore":  "use /chore to track this maintenance task",
    }

    # ── Intent detection (single-pass regex with named groups) ─────────────────
    intent_cmd = None
    best = None
    scores = {}
    if intent_match:
        # Extract the matched group name (intent category)
        best = intent_match.lastgroup
        if best:
            scores[best] = 1  # Single-pass match = score 1
            if best == "init" and (cwd / "zie-framework" / ".config").exists():
                pass  # already initialized — suppress init suggestion
            else:
                intent_cmd = SUGGESTIONS[best]

    # ── SDLC context (unified cache — session-scoped with TTL) ──────────
    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
    cache = get_cache_manager(cwd)
    roadmap_ttl = CACHE_TTLS.get("roadmap", 600)
    roadmap_content = cache.get_or_compute(
        "roadmap", session_id, lambda: roadmap_path.read_text(), roadmap_ttl
    )
    now_items = parse_roadmap_section_content(roadmap_content, "now") if roadmap_content else []
    if now_items:
        raw_task = now_items[0]
        active_task = raw_task[:80]
        stage = derive_stage(active_task)
    else:
        active_task = "none"
        stage = "idle"

    suggested_cmd = STAGE_COMMANDS.get(stage, "/status")
    test_status = get_test_status(cwd)

    # ── New-intent scoring (≥2 threshold) ─────────────────────────────────────
    # Sprint only fires when idle (no active Now lane item); fix/chore always fire.
    for intent_name, compiled_regexes in NEW_INTENT_REGEXES.items():
        if intent_name == "sprint" and active_task != "none":
            continue  # user has planned work — they're already in the pipeline
        score = sum(1 for p in compiled_regexes if p.search(message))
        if score >= 2:
            hint = NEW_INTENT_HINTS[intent_name]
            context = f"[zie-framework] intent: {intent_name} — {hint}"
            _should_emit = True
            if session_id != "default":
                _dp = _dedup_path(session_id, cwd)
                if _read_dedup(_dp) == context:
                    _should_emit = False
                else:
                    _write_dedup(_dp, context)
            if _should_emit:
                print(json.dumps({"additionalContext": context}))
            if intent_name == "sprint":
                try:
                    sprint_flag = project_tmp_path("intent-sprint-flag", cwd.name)
                    sprint_flag.write_text("active")
                except Exception:
                    pass
            sys.exit(0)

    # ── Pipeline gate check ───────────────────────────────────────────────────
    gate_msg = None
    if best and best == "plan":
        gate_msg = _check_pipeline_preconditions(best, roadmap_content, cwd, message)

    # ── No-active-track check ─────────────────────────────────────────────────
    no_track_msg = None
    if gate_msg is None and best in ("implement", "fix"):
        if not is_track_active(cwd):
            no_track_msg = (
                "no active track — pick one: "
                "standard: /backlog → /spec → /plan → /implement | "
                "hotfix: /hotfix | "
                "spike: /spike | "
                "chore: /chore"
            )

    # ── Positional guidance (only when no gate and no dominant intent) ────────
    guidance_msg = None
    if gate_msg is None and no_track_msg is None and (not intent_cmd or best == "status"):
        guidance_msg = _positional_guidance(roadmap_content, cwd, message)

    # ── Read pattern aggregate for personalized thresholds ───────────────────
    _agg_path = project_tmp_path("pattern-aggregate", cwd.name)
    _pattern_agg: dict = {}
    try:
        if _agg_path.exists():
            _pattern_agg = json.loads(_agg_path.read_text())
    except Exception:
        pass  # Missing or corrupt aggregate — use defaults
    _most_common_stage = _pattern_agg.get("most_common_stage", "")

    # Suppress pipeline-position hint when user consistently works at implement stage
    # (they know the pipeline; don't nag with "start with /spec" on every message)
    _suppress_guidance = (
        guidance_msg is not None
        and _most_common_stage == "implement"
        and best in ("implement", "status")
    )

    # ── Build combined context ────────────────────────────────────────────────
    parts = []
    if gate_msg:
        parts.append(gate_msg)
    elif no_track_msg:
        parts.append(no_track_msg)
    elif intent_cmd:
        parts.append(f"intent:{best} → {intent_cmd}")
    if guidance_msg and not _suppress_guidance:
        parts.append(guidance_msg)
    # State suffix: omit when idle + no active task + unambiguous intent (score >= 2)
    _best_score = scores.get(best, 0) if best else 0
    _idle_unambiguous = (stage == "idle" and active_task == "none" and _best_score >= 2)
    if not _idle_unambiguous:
        parts.append(
            f"task:{active_task} | stage:{stage} | next:{suggested_cmd} | tests:{test_status}"
        )
    context = "[zie-framework] " + " | ".join(parts)

    # ── Dedup: skip re-injection when context unchanged since last emission ──────
    if session_id != "default":
        _dp = _dedup_path(session_id, cwd)
        if _read_dedup(_dp) == context:
            sys.exit(0)
        _write_dedup(_dp, context)

    print(json.dumps({"additionalContext": context}))

except Exception as e:
    print(f"[zie-framework] intent-sdlc: {e}", file=sys.stderr)
    sys.exit(0)
