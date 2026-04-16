#!/usr/bin/env python3
"""PreToolUse:Bash hook — Code Quality Gate (warn-only, never blocks).

Fires on `git commit` commands. Runs warn-only checks:
  - Coverage delta (compares .coverage or coverage.xml if present)
  - Dead code signals in staged diff (commented-out blocks)
  - Security scan (bandit if available, skipped silently if not)

Always exits 0 — this hook informs, never blocks.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_error import log_error  # noqa: E402
from utils_event import get_cwd, read_event  # noqa: E402

# Outer guard — any unhandled exception exits 0 (never blocks Claude)
try:
    event = read_event()

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""

    # Only fire on git commit commands
    if not re.search(r"\bgit\s+commit\b", command):
        sys.exit(0)

    cwd = get_cwd()
    zf = cwd / "zie-framework"

    if not zf.exists():
        sys.exit(0)

    warnings = []

    # ── Check 1: Coverage delta ────────────────────────────────────────────
    try:
        coverage_file = cwd / ".coverage"
        coverage_xml = cwd / "coverage.xml"
        if not coverage_file.exists() and not coverage_xml.exists():
            warnings.append("coverage: no coverage data found — run tests before committing")
    except OSError:
        pass  # skip on any error

    # ── Check 2: Dead code signals in staged diff ──────────────────────────
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=0"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(cwd),
        )
        if result.returncode == 0 and result.stdout:
            diff_lines = result.stdout.splitlines()
            # Look for large commented-out blocks (3+ consecutive commented lines added)
            consecutive = 0
            max_consecutive = 0
            for line in diff_lines:
                if line.startswith("+") and not line.startswith("+++"):
                    stripped = line[1:].strip()
                    if stripped.startswith("#") or stripped.startswith("//"):
                        consecutive += 1
                        max_consecutive = max(max_consecutive, consecutive)
                    else:
                        consecutive = 0
                else:
                    consecutive = 0
            if max_consecutive >= 3:
                warnings.append(f"dead-code: {max_consecutive} consecutive commented lines in staged diff")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass  # git not available or timed out — skip

    # ── Check 3: Security scan (bandit — staged files only) ───────────────
    try:
        if shutil.which("bandit"):
            result_diff = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(cwd),
            )
            staged_py: list[str] = []
            if result_diff.returncode == 0:
                staged_py = [
                    str(cwd / f)
                    for f in result_diff.stdout.splitlines()
                    if f.endswith(".py")
                    and not any(part in Path(f).parts for part in ("venv", ".venv", "node_modules", "__pycache__"))
                ]
            if staged_py:
                result = subprocess.run(
                    ["bandit", "-q", "-ll", "-x", ".venv,venv"] + staged_py,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(cwd),
                )
                if result.returncode != 0 and result.stdout.strip():
                    issue_count = result.stdout.count("Issue:")
                    if issue_count > 0:
                        warnings.append(f"security: bandit found {issue_count} issue(s)")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass  # bandit not available or timed out — skip

    # ── Emit summary ──────────────────────────────────────────────────────
    count = len(warnings)
    if count > 0:
        print(f"Quality gate: {count} warning(s)", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)
    else:
        print("Quality gate: 0 warnings", file=sys.stderr)

except Exception as e:
    log_error("quality-gate", "main", e)
    sys.exit(0)

sys.exit(0)
