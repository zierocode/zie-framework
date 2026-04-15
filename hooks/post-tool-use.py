#!/usr/bin/env python3
"""Post-tool-use hook — proactive suggestions (auto-decide).

Analyzes tool output and presents context-aware suggestions at key moments.
Non-blocking: users can skip suggestions easily.

Triggered on PostToolUse event for Bash (test runs) and Write/Edit (file changes).
Always exits 0 — never blocks Claude.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_error import log_error
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path

# Suggestion frequency limits
_MAX_SUGGESTIONS_PER_SESSION = 3
_SUGGESTION_COOLDOWN_SECONDS = 300  # 5 minutes

# Trigger patterns
_TEST_FAILURE_PATTERNS = [
    re.compile(r"FAILED", re.IGNORECASE),
    re.compile(r"AssertionError", re.IGNORECASE),
    re.compile(r"ERROR", re.IGNORECASE),
    re.compile(r"pytest.*failed", re.IGNORECASE),
]

_MULTIPLE_ERROR_PATTERNS = [
    re.compile(r"(ERROR|FAILED|AssertionError)", re.IGNORECASE),
]

# Suggestion templates
_SUGGESTION_TEMPLATES = {
    "test_failure": """## Suggestion

**Detected:** {error_count} test(s) failing

**Recommended action:** Run `/fix` to debug and fix failing tests

**Why:** Failing tests block progress to next phase

> Skip: type "skip" or continue with another command""",

    "multiple_errors": """## Suggestion

**Detected:** {error_count} similar errors in output

**Recommended action:** Review error pattern and fix root cause

**Why:** Multiple similar errors suggest a common underlying issue

> Skip: type "skip" or continue with another command""",

    "spec_complete": """## Suggestion

**Detected:** Spec file written ({spec_name})

**Recommended action:** Run `/plan {slug}` to draft implementation plan

**Why:** Plan required before implementation can begin

> Skip: type "skip" or continue with another command""",

    "plan_complete": """## Suggestion

**Detected:** Plan file written ({plan_name})

**Recommended action:** Run `/implement` to start TDD implementation

**Why:** Ready to begin implementation with approved plan

> Skip: type "skip" or continue with another command""",
}


def _get_suggestion_state(cwd, session_id):
    """Load suggestion frequency state."""
    state_file = project_tmp_path("suggestion-state", cwd.name)
    try:
        if state_file.exists():
            data = json.loads(state_file.read_text())
            # Validate session ID
            if data.get("session_id") == session_id:
                return data
    except (json.JSONDecodeError, OSError):
        pass  # corrupt or missing state file — reset
    except Exception as e:
        log_error("post-tool-use", "load_suggestion_state", e)
    return {"session_id": session_id, "count": 0, "last_suggestion": None}


def _save_suggestion_state(cwd, state):
    """Save suggestion frequency state."""
    state_file = project_tmp_path("suggestion-state", cwd.name)
    try:
        state_file.write_text(json.dumps(state))
        os.chmod(state_file, 0o600)
    except (json.JSONDecodeError, OSError):
        pass  # state write failure — non-fatal, will reset next load
    except Exception as e:
        log_error("post-tool-use", "save_suggestion_state", e)


def _check_frequency_cap(state, priority="MEDIUM"):
    """Check if suggestion frequency cap allows this suggestion."""
    # HIGH priority bypasses cooldown
    if priority == "HIGH":
        return state["count"] < _MAX_SUGGESTIONS_PER_SESSION

    # Check max suggestions
    if state["count"] >= _MAX_SUGGESTIONS_PER_SESSION:
        return False

    # Check cooldown
    if state.get("last_suggestion"):
        try:
            last_time = datetime.fromisoformat(state["last_suggestion"])
            now = datetime.now(timezone.utc)
            if (now - last_time).total_seconds() < _SUGGESTION_COOLDOWN_SECONDS:
                return False
        except ValueError:
            pass  # invalid date format — treat as no cooldown
        except Exception as e:
            log_error("post-tool-use", "check_frequency_cap", e)

    return True


def _detect_test_failure(tool_result):
    """Detect test failure from Bash tool result."""
    if tool_result.get("tool") != "Bash":
        return False, 0

    command = tool_result.get("command", "")
    if "pytest" not in command and "test" not in command:
        return False, 0

    output = tool_result.get("output", "") + tool_result.get("stderr", "")
    exit_code = tool_result.get("exit_code", 0)

    if exit_code != 0:
        # Count failed tests
        error_count = sum(1 for pattern in _TEST_FAILURE_PATTERNS for _ in pattern.findall(output))
        return True, max(error_count, 1)

    return False, 0


def _detect_multiple_errors(tool_result):
    """Detect 3+ similar errors in output."""
    output = tool_result.get("output", "") + tool_result.get("stderr", "")

    error_count = 0
    for pattern in _MULTIPLE_ERROR_PATTERNS:
        error_count += len(pattern.findall(output))

    return error_count >= 3, error_count


def _detect_spec_complete(event, cwd):
    """Detect spec file written."""
    tool_result = event.get("tool_result", {})
    tool_name = tool_result.get("tool", "")
    if tool_name not in ["Write", "Edit"]:
        return False, None, None

    file_path = tool_result.get("input", {}).get("file_path", "")
    if "specs" in file_path and file_path.endswith(".md"):
        # Extract slug from filename (format: YYYY-MM-DD-slug-design.md)
        slug_match = re.search(r"\d{4}-\d{2}-\d{2}-(.+)-design\.md", file_path)
        if slug_match:
            slug = slug_match.group(1)
            return True, file_path, slug

    return False, None, None


def _detect_plan_complete(event, cwd):
    """Detect plan file written."""
    tool_result = event.get("tool_result", {})
    tool_name = tool_result.get("tool", "")
    if tool_name not in ["Write", "Edit"]:
        return False, None, None

    file_path = tool_result.get("input", {}).get("file_path", "")
    if "plans" in file_path and file_path.endswith(".md"):
        # Extract slug from filename (format: slug.md or YYYY-MM-DD-slug.md)
        slug_match = re.search(r"([^/]+)\.md$", file_path)
        if slug_match:
            slug = slug_match.group(1)
            # Skip if it's a design doc or other plan metadata
            if "design" not in slug.lower():
                return True, file_path, slug

    return False, None, None


def _generate_suggestion(trigger_type, **kwargs):
    """Generate formatted suggestion."""
    template = _SUGGESTION_TEMPLATES.get(trigger_type)
    if not template:
        return None
    return template.format(**kwargs)


def _get_priority(trigger_type):
    """Get trigger priority level."""
    high_priority = ["test_failure", "multiple_errors"]
    return "HIGH" if trigger_type in high_priority else "MEDIUM"


# Main execution
try:
    event = read_event()
    if not event:
        sys.exit(0)

    cwd = get_cwd()
    session_id = os.environ.get("CLAUDE_SESSION_ID", datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"))

    # Load suggestion state
    state = _get_suggestion_state(cwd, session_id)

    # Detect triggers
    tool_result = event.get("tool_result", {})
    suggestion = None
    trigger_type = None
    trigger_data = {}

    # Test failure detection (HIGH priority)
    is_failure, error_count = _detect_test_failure(tool_result)
    if is_failure:
        trigger_type = "test_failure"
        trigger_data = {"error_count": error_count}

    # Multiple errors detection (HIGH priority)
    if not trigger_type:
        is_multiple, error_count = _detect_multiple_errors(tool_result)
        if is_multiple:
            trigger_type = "multiple_errors"
            trigger_data = {"error_count": error_count}

    # Spec complete detection (MEDIUM priority)
    if not trigger_type:
        is_complete, file_path, slug = _detect_spec_complete(event, cwd)
        if is_complete and slug:
            trigger_type = "spec_complete"
            trigger_data = {"spec_name": file_path.split("/")[-1], "slug": slug}

    # Plan complete detection (MEDIUM priority)
    if not trigger_type:
        is_complete, file_path, slug = _detect_plan_complete(event, cwd)
        if is_complete and slug:
            trigger_type = "plan_complete"
            trigger_data = {"plan_name": file_path.split("/")[-1], "slug": slug}

    # Generate and present suggestion
    if trigger_type:
        priority = _get_priority(trigger_type)

        if _check_frequency_cap(state, priority):
            suggestion = _generate_suggestion(trigger_type, **trigger_data)

            if suggestion:
                # Output suggestion via additionalContext
                print(json.dumps({"additionalContext": suggestion}))

                # Update state
                state["count"] += 1
                state["last_suggestion"] = datetime.now(timezone.utc).isoformat()
                _save_suggestion_state(cwd, state)

    sys.exit(0)

except Exception as e:
    # Never block Claude on hook failure
    print(f"[zie-framework] post-tool-use: {e}", file=sys.stderr)
    sys.exit(0)
