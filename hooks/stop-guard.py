#!/usr/bin/env python3
"""Stop hook — block if uncommitted implementation files are detected.

Emits {"decision": "block", "reason": "..."} to stdout when git status
reports uncommitted hooks/*.py, tests/*.py, commands/*.md, skills/**/*.md,
or templates/**/* files. Exits 0 on all error paths (ADR-003).

Infinite-loop guard: if event["stop_hook_active"] is truthy, the hook
has already fired once for this continuation cycle — exit immediately
without running git, preventing Claude from being blocked indefinitely.
"""
import fnmatch
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_config import load_config
from utils_roadmap import get_cached_git_status, parse_roadmap_items_with_dates, write_git_status_cache

# Canonical implementation file patterns for zie-framework layout.
# Paths are matched against the raw path token from `git status --short`
# (relative to repo root, e.g. "hooks/stop-guard.py").
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

def _run_nudges(cwd, config, subprocess_timeout):
    """Run proactive nudge checks. Each check is independent and silently skipped on error."""
    import datetime as _dt

    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"

    # Nudge 1: RED phase duration (git log based — skip if no git or no Now items)
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
                    import re as _re
                    slug_match = _re.search(r'\[([^\]]+)\]\(backlog/([^\)]+)\.md\)', line)
                    slug = slug_match.group(2) if slug_match else line.strip()
                    now_items_raw.append(slug)
        for slug in now_items_raw:
            try:
                import re as _re
                result = subprocess.run(
                    f"git log --all -p -- zie-framework/ROADMAP.md "
                    f"| grep -B5 '+- \\[ \\] {slug}'",
                    cwd=str(cwd),
                    capture_output=True,
                    text=True,
                    timeout=subprocess_timeout,
                    shell=True,  # nosec B602 — piped git log | grep, slug from ROADMAP (internal)
                )
                if result.returncode == 0 and result.stdout.strip():
                    date_match = _re.search(r'^Date:\s+(\d{4}-\d{2}-\d{2})', result.stdout, _re.MULTILINE)
                    if not date_match:
                        date_match = _re.search(r'(\d{4}-\d{2}-\d{2})', result.stdout)
                    if date_match:
                        commit_date = _dt.date.fromisoformat(date_match.group(1))
                        days = (_dt.date.today() - commit_date).days
                        if days > 2:
                            print(
                                f"[zie-framework] nudge: RED phase '{slug}' has been active for "
                                f"{days} days — consider splitting or committing partial progress"
                            )
            except Exception:
                pass
    except Exception:
        pass

    # Nudge 2: Coverage staleness
    try:
        tests_dir = cwd / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("*.py"))
            if test_files:
                newest_test_mtime = max(f.stat().st_mtime for f in test_files)
                cov_file = cwd / ".coverage"
                if not cov_file.exists():
                    print("[zie-framework] nudge: coverage data is stale — run 'make test-unit' to refresh")
                elif cov_file.stat().st_mtime < newest_test_mtime:
                    print("[zie-framework] nudge: coverage data is stale — run 'make test-unit' to refresh")
    except Exception:
        pass

    # Nudge 3: Stale backlog items in Next
    try:
        items_with_dates = parse_roadmap_items_with_dates(roadmap_path, "next")
        today = _dt.date.today()
        stale_count = sum(
            1 for _, d in items_with_dates
            if d is not None and (today - d).days > 30
        )
        if stale_count > 0:
            print(
                f"[zie-framework] nudge: {stale_count} backlog item(s) in Next are older than "
                "30 days — review or defer"
            )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Outer guard — parse stdin; never block Claude on failure
# ---------------------------------------------------------------------------
try:
    event = read_event()
    # Infinite-loop guard: Claude Code sets stop_hook_active on the Stop event
    # that follows a hook-triggered continuation. Exit immediately so the guard
    # fires at most once per original response.
    if event.get("stop_hook_active"):
        sys.exit(0)
except Exception:
    sys.exit(0)

# ---------------------------------------------------------------------------
# Inner operations — git status + filter
# ---------------------------------------------------------------------------
try:
    cwd = get_cwd()
    config = load_config(cwd)
    subprocess_timeout = config["subprocess_timeout_s"]
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")

    # Use session cache to avoid repeated git subprocess on every Stop event
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
        # Non-zero return code means not a git repo, detached HEAD, or bare repo.
        # Still run nudges even without git status.
        if result.returncode != 0:
            _run_nudges(cwd, config, subprocess_timeout)
            sys.exit(0)
        status_output = result.stdout
        write_git_status_cache(session_id, "status", status_output)

    uncommitted = []
    for line in status_output.splitlines():
        if len(line) < 4:
            continue
        # git status --short format: XY<space>path
        # XY is two chars; char index 0=staged, 1=unstaged; path starts at [3:]
        path_token = line[3:].strip()
        # Strip rename arrows: "old -> new" — take the destination
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

    # --- Proactive nudges ---
    _run_nudges(cwd, config, subprocess_timeout)
    sys.exit(0)

except Exception as e:
    print(f"[zie-framework] stop-guard: {e}", file=sys.stderr)
    sys.exit(0)
