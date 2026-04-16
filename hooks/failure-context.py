#!/usr/bin/env python3
"""PostToolUseFailure hook — inject SDLC debug context on tool failure."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_config import load_config
from utils_error import log_error
from utils_event import get_cwd, read_event
from utils_roadmap import (
    get_cached_git_status,
    parse_roadmap_section_content,
    read_roadmap_cached,
    write_git_status_cache,
)

ALLOWED_TOOLS = {"Bash", "Write", "Edit"}

# ── Outer guard ──────────────────────────────────────────────────────────────

try:
    event = read_event()
except (json.JSONDecodeError, OSError):
    sys.exit(0)
except Exception as e:
    log_error("failure-context", "read_event", e)
    sys.exit(0)

try:
    if event.get("is_interrupt", False):
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    if tool_name not in ALLOWED_TOOLS:
        sys.exit(0)
except (json.JSONDecodeError, OSError):
    sys.exit(0)
except Exception as e:
    log_error("failure-context", "early_exit_guard", e)
    sys.exit(0)

# ── Inner operations ─────────────────────────────────────────────────────────

try:
    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)
    config = load_config(cwd)
    subprocess_timeout = config["subprocess_timeout_s"]
    session_id = event.get("session_id", "default")

    # ROADMAP Now lane (via session cache)
    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
    try:
        roadmap_content = read_roadmap_cached(roadmap_path, session_id)
        now_items = parse_roadmap_section_content(roadmap_content, "now")
    except OSError as e:
        log_error("failure-context", "roadmap_read", e)
        now_items = []
    except Exception as e:
        log_error("failure-context", "roadmap_read", e)
        now_items = []
    active_task = now_items[0] if now_items else "(none — check ROADMAP Now lane)"

    # Git last commit (with session cache, 5s TTL)
    try:
        cached = get_cached_git_status(session_id, "log")
        if cached is not None:
            last_commit = cached
        else:
            log_result = subprocess.run(
                ["git", "log", "-1", "--pretty=%h %s"],
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=subprocess_timeout,
            )
            last_commit = log_result.stdout.strip() if log_result.returncode == 0 else "(git unavailable)"
            if log_result.returncode == 0:
                write_git_status_cache(session_id, "log", last_commit)
    except subprocess.TimeoutExpired as e:
        log_error("failure-context", "git_log", e)
        last_commit = "(git unavailable)"
    except OSError as e:
        log_error("failure-context", "git_log", e)
        last_commit = "(git unavailable)"
    except Exception as e:
        log_error("failure-context", "git_log", e)
        last_commit = "(git unavailable)"

    # Git branch (with session cache, 5s TTL)
    try:
        cached = get_cached_git_status(session_id, "branch")
        if cached is not None:
            branch = cached
        else:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=subprocess_timeout,
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "(git unavailable)"
            if branch_result.returncode == 0:
                write_git_status_cache(session_id, "branch", branch)
    except subprocess.TimeoutExpired as e:
        log_error("failure-context", "git_branch", e)
        branch = "(git unavailable)"
    except OSError as e:
        log_error("failure-context", "git_branch", e)
        branch = "(git unavailable)"
    except Exception as e:
        log_error("failure-context", "git_branch", e)
        branch = "(git unavailable)"

    # Build context string
    context_string = (
        f"[SDLC context at failure]\nActive task: {active_task}\nBranch: {branch}\nLast commit: {last_commit}"
    )

    print(json.dumps({"additionalContext": context_string}))

except Exception as e:
    print(f"[zie-framework] failure-context: {e}", file=sys.stderr)

sys.exit(0)
