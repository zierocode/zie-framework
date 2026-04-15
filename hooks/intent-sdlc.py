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
from utils_event import get_cwd, read_event
from utils_config import CACHE_TTLS
from utils_cache import get_cache_manager
from utils_roadmap import is_track_active, parse_roadmap_section_content
from utils_skill_inject import inject_skill_context

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

# New-intent scoring: separate patterns for overlapping detection.
# INTENT_PATTERN uses alternation (|) so only the first matching group is
# populated — named groups that appear later in the alternation are never tried.
# These separate patterns allow us to detect multiple signals in one message.
NEW_INTENT_PATTERNS = {
    "sprint": re.compile(
        r"\bbuild\b | \bsprint\b | ทำเลย | สร้าง | เพิ่ม.*feature | start\s*coding",
        re.IGNORECASE | re.VERBOSE,
    ),
    "fix": re.compile(
        r"\bbroken\b | ไม่.*work | \bcrash\b | \bfail\b | แก้",
        re.IGNORECASE | re.VERBOSE,
    ),
    "chore": re.compile(
        r"\bupdate\b | \bbump\b | \brename\b | \bcleanup\b | \brefactor\b | ลบ",
        re.IGNORECASE | re.VERBOSE,
    ),
}
NEW_INTENT_HINTS = {
    "sprint": "confirm backlog→spec→plan before implementing",
    "fix":    "invoke /fix or /hotfix track",
    "chore":  "use /chore to track this maintenance task",
}

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
            f"⛔ No approved spec for {slug_list}. "
            f"Run /spec {blocking[0]} first."
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
        return f"backlog:{slug} → /spec {slug}"
    if has_approved_spec and not slug_in_ready:
        return f"spec:{slug} ✓ → /plan {slug}"
    return f"plan:{slug} ✓ → /implement"


def derive_stage(task_text: str) -> str:
    main = task_text.split("—")[0].strip()
    lower = main.lower()
    for stage, keywords in STAGE_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return stage
    return "in-progress"


def get_test_status(cwd: Path) -> str:
    try:
        cache = get_cache_manager(cwd)
        ts = cache.get("last-test", "_global")
        if ts is not None:
            age = time.time() - float(ts)
            return "stale" if age > STALE_THRESHOLD_SECS else "recent"
    except Exception:
        pass
    return "unknown"


_DEDUP_TTL_SECS = 600  # 10-minute session window


def _read_dedup(cache, session_id: str, key: str) -> str:
    """Return last emitted context string from CacheManager, or '' on miss."""
    try:
        val = cache.get(key, session_id)
        return val if isinstance(val, str) else ""
    except Exception:
        return ""


def _write_dedup(cache, session_id: str, key: str, context: str) -> None:
    """Write current context to CacheManager dedup cache."""
    try:
        cache.set(key, context, session_id, ttl=_DEDUP_TTL_SECS)
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
    cache = get_cache_manager(cwd)

    # ── Early-exit guard (short + zero SDLC keywords → unclear intent) ─────────
    # Single-pass regex match for all 17 intent categories (14 original + 3 new-intent)
    intent_match = INTENT_PATTERN.search(message)
    has_sdlc_keyword = intent_match is not None

    # Strong-intent groups that bypass the short-message gate even under 50 chars
    _STRONG_INTENT_GROUPS = {
        "init", "sprint", "hotfix", "fix", "implement", "spec", "plan", "release", "retro", "status",
    }
    _has_strong_intent = (
        intent_match is not None
        and intent_match.lastgroup in _STRONG_INTENT_GROUPS
    )

    if len(message) < 50:
        if not has_sdlc_keyword:
            context = (
                "[zf] intent: unclear — clarify before proceeding"
            )
            if session_id != "default":
                _dedup_key = f"intent-dedup-{session_id}"
                if _read_dedup(cache, session_id, _dedup_key) == context:
                    sys.exit(0)
                _write_dedup(cache, session_id, _dedup_key, context)
            print(json.dumps({"additionalContext": context}))
            sys.exit(0)
        if not _has_strong_intent:
            sys.exit(0)  # short with weak keyword → exit

    if not has_sdlc_keyword:
        sys.exit(0)

    # ── SDLC context (unified cache — session-scoped with TTL) ──────────
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

    # ── New-intent scoring from separate patterns (≥2 threshold) ────────────────
    # Use NEW_INTENT_PATTERNS for overlapping detection since INTENT_PATTERN's
    # alternation only populates the first matching named group.
    _BOOST_GROUPS = {"sprint": "implement", "fix": "fix", "chore": "chore"}
    for intent_name, pattern in NEW_INTENT_PATTERNS.items():
        if intent_name == "sprint" and active_task != "none":
            continue  # user has planned work — they're already in the pipeline
        if pattern.search(message):
            count = 1
            boost_group = _BOOST_GROUPS.get(intent_name)
            if boost_group and intent_match and intent_match.lastgroup == boost_group:
                count = 2
            for other_name, other_pattern in NEW_INTENT_PATTERNS.items():
                if other_name != intent_name and other_pattern.search(message):
                    count += 1
            if count >= 2:
                hint = NEW_INTENT_HINTS[intent_name]
                context = f"[zf] intent: {intent_name} — {hint}"
                _should_emit = True
                if session_id != "default":
                    _dedup_key = f"intent-new-{intent_name}-{session_id}"
                    if _read_dedup(cache, session_id, _dedup_key) == context:
                        _should_emit = False
                    else:
                        _write_dedup(cache, session_id, _dedup_key, context)
                if _should_emit:
                    print(json.dumps({"additionalContext": context}))
                if intent_name == "sprint":
                    try:
                        cache.set_flag("intent-sprint-flag", session_id)
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
                "no track — /backlog→/spec→/plan→/implement | /hotfix | /spike | /chore"
            )

    # ── Positional guidance (only when no gate and no dominant intent) ────────
    guidance_msg = None
    if gate_msg is None and no_track_msg is None and (not intent_cmd or best == "status"):
        guidance_msg = _positional_guidance(roadmap_content, cwd, message)

    # ── Read pattern aggregate for personalized thresholds ───────────────────
    _pattern_agg: dict = {}
    try:
        _cached_agg = cache.get("pattern-aggregate", session_id)
        if isinstance(_cached_agg, dict):
            _pattern_agg = _cached_agg
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
        parts.append(f"intent:{best}→{intent_cmd}")
    if guidance_msg and not _suppress_guidance:
        parts.append(guidance_msg)
    # State suffix: omit when idle + no active task + unambiguous intent (score >= 2)
    _best_score = scores.get(best, 0) if best else 0
    _idle_unambiguous = (stage == "idle" and active_task == "none" and _best_score >= 2)
    if not _idle_unambiguous:
        parts.append(
            f"now:{active_task} stage:{stage} next:{suggested_cmd} tests:{test_status}"
        )
    context = "[zf] " + " | ".join(parts)

    # ── Skill auto-inject ────────────────────────────────────────────────────────
    _skill_content = inject_skill_context(best or stage, cwd)
    if _skill_content:
        context += "\n\n" + _skill_content

    # ── Dedup: skip re-injection when context unchanged since last emission ──────
    if session_id != "default":
        _dedup_key = f"intent-dedup-{session_id}"
        if _read_dedup(cache, session_id, _dedup_key) == context:
            sys.exit(0)
        _write_dedup(cache, session_id, _dedup_key, context)

    print(json.dumps({"additionalContext": context}))

except Exception as e:
    print(f"[zf] intent-sdlc: {e}", file=sys.stderr)
    sys.exit(0)
