#!/usr/bin/env python3
"""Unified Stop handler — consolidates stop-guard, stop-pipeline-guard, compact-hint.

Single git status call, combined nudge checks, one log entry.
Always exits 0 (ADR-003) — never blocks Claude.
Infinite-loop guard: exits immediately when stop_hook_active is truthy.
"""

import fnmatch
import json
import os
import re
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from utils_cache import get_cache_manager
from utils_config import load_config
from utils_error import log_error
from utils_event import get_cwd, read_event
from utils_roadmap import get_cached_git_status, parse_roadmap_items_with_dates, write_git_status_cache

# Canonical implementation file patterns for zie-framework layout.
IMPL_PATTERNS = [
    "hooks/*.py",
    "tests/*.py",
    "commands/*.md",
    "skills/*.md",
    "skills/*/*.md",
    "templates/*",
    "templates/*/*",
    "templates/*/*/*",
]


def _run_combined_nudges(cwd, config, subprocess_timeout, git_status_output, session_id, event=None):
    """Run all nudge checks in a single pass with shared git log output."""
    import datetime as _dt

    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"

    # Single git log call for all log-based nudges
    git_log_output = None
    try:
        result = subprocess.run(
            ["git", "log", "--all", "-p", "--", "zie-framework/ROADMAP.md"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=subprocess_timeout,
            shell=False,
        )
        if result.returncode == 0:
            git_log_output = result.stdout
    except (OSError, subprocess.TimeoutExpired) as _e:
        log_error("stop-handler", "git_log", _e)

    # Nudge 1: RED phase duration (git log based)
    if git_log_output:
        try:
            now_items_raw = []
            if roadmap_path.exists():
                content = roadmap_path.read_text()
                in_now = False
                for line in content.splitlines():
                    if line.startswith("##") and "now" in line.lower():
                        in_now = True
                        continue
                    if line.startswith("##") and in_now:
                        break
                    if in_now and "[ ]" in line:
                        slug_match = re.search(r"\[([^\]]+)\]\(backlog/([^\)]+)\.md\)", line)
                        slug = slug_match.group(2) if slug_match else line.strip()
                        now_items_raw.append(slug)

            for slug in now_items_raw:
                try:
                    slug_pattern = re.compile(r"^\+- \[ \] " + re.escape(slug))
                    lines = git_log_output.splitlines()
                    date_match = None
                    for i, line in enumerate(lines):
                        if slug_pattern.match(line):
                            for j in range(max(0, i - 5), i):
                                dm = re.search(r"^Date:\s+(\d{4}-\d{2}-\d{2})", lines[j])
                                if dm:
                                    date_match = dm
                                    break
                            if date_match:
                                break
                    if date_match:
                        commit_date = _dt.date.fromisoformat(date_match.group(1))
                        days = (_dt.date.today() - commit_date).days
                        if days > 2:
                            print(
                                f"[zie-framework] nudge: RED phase '{slug}' has been "
                                f"active for {days} days — consider splitting or committing"
                            )
                except (re.error, ValueError, OSError) as _e:
                    log_error("stop-handler", "slug_date_parse", _e)
        except Exception as _e:
            log_error("stop-handler", "nudge_git_log", _e)

    # Nudge 2: Coverage staleness
    try:
        tests_dir = cwd / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("*.py"))
            if test_files:
                newest_test_mtime = max(f.stat().st_mtime for f in test_files)
                cov_file = cwd / ".coverage"
                if not cov_file.exists():
                    print("[zie-framework] nudge: coverage data is stale — run 'make test-unit'")
                elif cov_file.stat().st_mtime < newest_test_mtime:
                    print("[zie-framework] nudge: coverage data is stale — run 'make test-unit'")
    except (OSError, FileNotFoundError) as _e:
        log_error("stop-handler", "coverage_staleness", _e)

    # Nudge 3: Stale backlog items in Next
    try:
        items_with_dates = parse_roadmap_items_with_dates(roadmap_path, "next")
        today = _dt.date.today()
        stale_count = sum(1 for _, d in items_with_dates if d is not None and (today - d).days > 30)
        if stale_count > 0:
            print(
                f"[zie-framework] nudge: {stale_count} backlog item(s) in Next are older than 30 days — review or defer"
            )
    except (OSError, ValueError) as _e:
        log_error("stop-handler", "stale_backlog_nudge", _e)

    # Nudge 4: Sprint intent without approved artifacts (from stop-pipeline-guard)
    try:
        cache = get_cache_manager(cwd)
        if cache.has_flag("intent-sprint-flag", session_id):
            today = date.today().isoformat()
            found_approved = False
            zf = cwd / "zie-framework"
            if zf.exists():
                for subdir in ("specs", "plans"):
                    target_dir = zf / subdir
                    if not target_dir.exists():
                        continue
                    for md_file in target_dir.glob("*.md"):
                        try:
                            mtime = _dt.date.fromtimestamp(md_file.stat().st_mtime).isoformat()
                            if mtime != today:
                                continue
                            content = md_file.read_text()
                            if re.search(r"^approved:\s*true\s*$", content, re.MULTILINE):
                                found_approved = True
                                break
                        except (OSError, FileNotFoundError) as _e:
                            log_error("stop-handler", "artifact_mtime", _e)
                            continue
                    if found_approved:
                        break

            if not found_approved:
                print(
                    "[zf] sprint intent detected but no approved spec/plan found "
                    "this session\n  → Run /spec <feature> then /plan <feature> before implementing"
                )

            # Cleanup flag
            cache.delete("intent-sprint-flag", session_id)
    except Exception as _e:
        log_error("stop-handler", "sprint_intent_nudge", _e)

    # Nudge 5: Context window health (from compact-hint)
    try:
        if event is None:
            event = read_event()
        context_window = event.get("context_window") if event else None
        if isinstance(context_window, dict):
            current = context_window.get("current_tokens")
            max_tokens = context_window.get("max_tokens")
            if current is not None and max_tokens:
                pct = current / max_tokens
                pct_int = int(pct * 100)

                session_id = event.get("session_id", "")
                cache = get_cache_manager(cwd)

                advisory_threshold = config.get("compact_advisory_threshold", 0.75)
                mandatory_threshold = config.get("compact_mandatory_threshold", 0.90)

                if pct >= mandatory_threshold:
                    if not cache.has_flag("compact-tier-mandatory", session_id):
                        print(
                            f"[zf] Context at {pct_int}% — start a fresh session."
                        )
                        cache.set_flag("compact-tier-mandatory", session_id)
                elif pct >= advisory_threshold:
                    if not cache.has_flag("compact-tier-advisory", session_id):
                        print(f"[zf] Context at {pct_int}% — /compact soon recommended.")
                        cache.set_flag("compact-tier-advisory", session_id)
    except Exception as _e:
        log_error("stop-handler", "context_window_nudge", _e)


# ---------------------------------------------------------------------------
# Outer guard — parse stdin; never block Claude on failure
# ---------------------------------------------------------------------------
try:
    event = read_event()
    # Infinite-loop guard
    if event.get("stop_hook_active"):
        sys.exit(0)
except (json.JSONDecodeError, OSError, AttributeError):
    sys.exit(0)

# ---------------------------------------------------------------------------
# Inner operations — git status + filter + combined nudges
# ---------------------------------------------------------------------------
try:
    cwd = get_cwd()
    config = load_config(cwd)
    subprocess_timeout = config["subprocess_timeout_s"]
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")

    # Use session cache to avoid repeated git subprocess
    cached = get_cached_git_status(session_id, "status")
    if cached is not None:
        status_output = cached
    else:
        result = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=subprocess_timeout,
        )
        if result.returncode != 0:
            # Not a git repo — still run nudges
            if not session_id:
                _run_combined_nudges(cwd, config, subprocess_timeout, "", session_id, event)
            else:
                _nudge_cached_early = get_cached_git_status(session_id, "nudge-check", ttl=1800)
                if _nudge_cached_early is None:
                    write_git_status_cache(session_id, "nudge-check", "1")
                    _run_combined_nudges(cwd, config, subprocess_timeout, "", session_id, event)
            sys.exit(0)
        status_output = result.stdout
        write_git_status_cache(session_id, "status", status_output)

    # Check for uncommitted implementation files
    uncommitted = []
    for line in status_output.splitlines():
        if len(line) < 4:
            continue
        path_token = line[3:].strip()
        if " -> " in path_token:
            path_token = path_token.split(" -> ", 1)[1].strip()
        if any(fnmatch.fnmatch(path_token, pat) for pat in IMPL_PATTERNS):
            uncommitted.append(path_token)

    if uncommitted:
        file_list = "\n".join(f"  {p}" for p in sorted(uncommitted))
        reason = (
            f"Uncommitted implementation files detected:\n{file_list}\n\n"
            "Commit this work before ending:\n"
            "  git add -A && git commit -m 'feat: <describe change>'"
        )
        print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)

    # Run combined nudges (session-scoped TTL gate — 30 min)
    if not session_id:
        _run_combined_nudges(cwd, config, subprocess_timeout, status_output, session_id, event)
    else:
        _nudge_cached = get_cached_git_status(session_id, "nudge-check", ttl=1800)
        if _nudge_cached is None:
            write_git_status_cache(session_id, "nudge-check", "1")
            _run_combined_nudges(cwd, config, subprocess_timeout, status_output, session_id, event)
    sys.exit(0)

except Exception as e:
    print(f"[zie-framework] stop-handler: {e}", file=sys.stderr)
    sys.exit(0)
