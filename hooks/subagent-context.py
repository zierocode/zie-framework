#!/usr/bin/env python3
"""SubagentStart hook — inject SDLC context into subagents per per-agent budget table.

ADR-046 superseded: the Explore/Plan-only guard is replaced by AGENT_BUDGETS
which handles all agent types explicitly with a conservative default for unknowns.

Session cache: first inject per session writes a flag; subsequent SubagentStart
events for the same project skip inject to avoid redundant context.
Content-hash cache: SHA-256 of (ADR summary + project context) with 600s TTL.
If content unchanged and TTL not expired, skip re-injection even across sessions.
"""
import hashlib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import atomic_write, project_tmp_path
from utils_roadmap import parse_roadmap_section_content, read_roadmap_cached

# Per-agent context budget table (supersedes ADR-046 Explore/Plan guard).
# Value: True = inject context; False = skip inject entirely.
AGENT_BUDGETS = {
    "spec-reviewer":  True,   # receives spec file + ADR summary
    "plan-reviewer":  True,   # receives plan + spec + ADR summary
    "impl-reviewer":  True,   # receives changed files + plan
    "resync":         True,   # receives git log + file structure
    "Explore":        True,
    "Plan":           True,
    "brainstorm":     False,  # skill has own Phase 1 discovery — no injection
}
_DEFAULT_INJECT = False  # conservative default: don't inject unknown agent types

# Content-hash cache TTL in seconds
_CONTENT_HASH_TTL = 600


# ── Helper ────────────────────────────────────────────────────────────────────────

def _compute_content_hash(cwd):
    """Compute SHA-256 hash of ADR summary + project context content.

    Returns hex digest string, or empty string if neither file exists.
    """
    hasher = hashlib.sha256()
    found = False
    for path in (
        cwd / "zie-framework" / "decisions" / "ADR-000-summary.md",
        cwd / "zie-framework" / "project" / "context.md",
    ):
        try:
            if path.exists():
                hasher.update(path.read_bytes())
                found = True
        except Exception:
            continue
    return hasher.hexdigest() if found else ""


# ── Outer guard ───────────────────────────────────────────────────────────────

try:
    event = read_event()
    agent_type = event.get("agentType", "")
    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Budget table check ────────────────────────────────────────────────────────

# Normalize: case-insensitive match against budget table keys
_should_inject = _DEFAULT_INJECT
for key, inject in AGENT_BUDGETS.items():
    if re.search(re.escape(key), agent_type, re.IGNORECASE):
        _should_inject = inject
        break

if not _should_inject:
    sys.exit(0)

# ── Content-hash cache check ────────────────────────────────────────────────────
# If ADR summary + project context unchanged since last injection (within 600s TTL),
# skip re-injection even across different sessions.

session_id = event.get("session_id", "")
project = cwd.name

content_hash = _compute_content_hash(cwd)
if content_hash:
    hash_file = project_tmp_path(f"context-hash-{project}", project)
    if hash_file.exists():
        try:
            stored = hash_file.read_text().splitlines()
            if len(stored) >= 2:
                stored_hash = stored[0]
                stored_time = float(stored[1])
                if stored_hash == content_hash and (time.time() - stored_time) < _CONTENT_HASH_TTL:
                    # Content unchanged and TTL valid — skip injection
                    sys.exit(0)
        except Exception:
            # Corrupt hash file — re-inject
            pass

# ── Session cache check ────────────────────────────────────────────────────────
# Cache is session-scoped: key on session_id so a new session always injects.
# If session_id is absent (spec: fallback to always-inject), skip cache entirely.

if session_id:
    safe_sid = re.sub(r'[^a-zA-Z0-9]', '-', session_id)
    cache_flag = project_tmp_path(f"session-context-{safe_sid}", project)
    if cache_flag.exists():
        flag_age = time.time() - cache_flag.stat().st_mtime
        if flag_age < 7200:
            # Already injected this session — skip to avoid redundant context
            sys.exit(0)
        # Stale flag (>2h) — delete and re-inject
        cache_flag.unlink(missing_ok=True)
else:
    cache_flag = None  # no session_id → always inject (spec fallback)

# ── Inner operations ──────────────────────────────────────────────────────────

feature_slug = "none"
active_task = "unknown"
adr_count = "unknown"

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

# Early exit when idle
if active_task == "none" and feature_slug == "none":
    sys.exit(0)

# Find most-recent plan file and extract first incomplete task (Plan agents only)
if re.search(r'Plan', agent_type, re.IGNORECASE):
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
else:
    active_task = "n/a"

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
if active_task == "n/a":
    payload = f"[zie-framework] Active: {feature_slug} | ADRs: {adr_count}"
else:
    payload = (
        f"[zie-framework] Active: {feature_slug} | "
        f"Task: {active_task} | "
        f"ADRs: {adr_count}"
    )
print(json.dumps({"additionalContext": payload}))

# Write session cache flag so subsequent SubagentStart events skip inject
# cache_flag is None when session_id was absent (spec fallback: always inject)
if cache_flag is not None:
    try:
        atomic_write(cache_flag, "cached")
    except Exception as e:
        print(f"[zie-framework] subagent-context: cache write failed: {e}", file=sys.stderr)
        # Non-fatal — next subagent will just inject again

# Write content-hash cache for cross-session dedup
if content_hash:
    try:
        hash_file = project_tmp_path(f"context-hash-{project}", project)
        atomic_write(hash_file, f"{content_hash}\n{time.time()}")
    except Exception as e:
        print(f"[zie-framework] subagent-context: hash cache write failed: {e}", file=sys.stderr)