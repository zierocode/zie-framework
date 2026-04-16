#!/usr/bin/env python3
"""PreToolUse:Write|Edit|Bash hook — unified safety check + quality gate + reviewer gate.

Execution order:
1. Write|Edit → reviewer gate check (block self-approval of specs/plans).
2. Write|Edit → relative path resolution (emits updatedInput + exit 0).
3. Bash → quality gate checks on git commit (warn-only).
4. Bash → evaluate() first; if exit 2, stop. If exit 0, run confirm-wrap.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import safety_check_agent
from utils_config import load_config
from utils_error import log_error
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path
from utils_safety import COMPILED_BLOCKS, COMPILED_WARNS, normalize_command

# Bash commands that warrant interactive confirmation.
CONFIRM_PATTERNS = [
    r"rm\s+-rf\s+\./",
    r"rm\s+-f\s+\./",
    r"git\s+clean\s+-fd",
    r"make\s+clean",
    r"truncate\s+--size\s+0",
]

_DANGEROUS_COMPOUND_RE = re.compile(r"(?:;|&&|\|\||`|\$\(|[{}>|<\n])")

# ── Reviewer gate (merged from reviewer-gate.py) ────────────────────────────
_APPROVED_TRUE_RE = re.compile(r"^approved:\s*true\s*$", re.MULTILINE)


def _is_spec_or_plan(file_path: str) -> bool:
    p = Path(file_path).as_posix()
    return "zie-framework/specs/" in p or "zie-framework/plans/" in p


def _already_approved(full_path: Path) -> bool:
    try:
        return bool(_APPROVED_TRUE_RE.search(full_path.read_text()))
    except (OSError, FileNotFoundError) as e:
        log_error("safety-check/reviewer-gate", "read_file", e)
        return False


def _check_reviewer_gate(tool_name, tool_input, cwd):
    """Block direct approved:true writes to spec/plan files."""
    if tool_name not in {"Write", "Edit"}:
        return 0  # allow

    file_path = tool_input.get("file_path", "")
    if not file_path or not _is_spec_or_plan(file_path):
        return 0  # allow

    content = tool_input.get("content", "") if tool_name == "Write" else tool_input.get("new_string", "")
    if not _APPROVED_TRUE_RE.search(content):
        return 0  # allow

    full_path = Path(file_path) if Path(file_path).is_absolute() else cwd / file_path
    if _already_approved(full_path):
        return 0  # idempotent — already approved

    kind = "spec" if "specs/" in file_path else "plan"
    skill = "zie-framework:review, 'phase=spec'" if kind == "spec" else "zie-framework:review, 'phase=plan'"
    print(
        f"[reviewer-gate] BLOCKED: Cannot self-approve {kind}.\n"
        f"\n"
        f"Step 1 — run the reviewer:\n"
        f"  Skill('{skill}')\n"
        f"\n"
        f"Step 2 — after reviewer returns \u2705 APPROVED, set approval via Bash:\n"
        f"  python3 hooks/approve.py {file_path}\n"
        f"\n"
        f"Writing approved:true directly is always blocked."
    )
    return 2  # block


# ── Quality gate (merged from quality-gate.py) ──────────────────────────────

def _run_quality_gate(command, cwd):
    """Warn-only checks on git commit commands."""
    if not re.search(r"\bgit\s+commit\b", command):
        return

    zf = cwd / "zie-framework"
    if not zf.exists():
        return

    warnings = []

    # Check 1: Coverage delta
    try:
        coverage_file = cwd / ".coverage"
        coverage_xml = cwd / "coverage.xml"
        if not coverage_file.exists() and not coverage_xml.exists():
            warnings.append("coverage: no coverage data found — run tests before committing")
    except OSError:
        pass

    # Check 2: Dead code signals in staged diff
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=0"],
            capture_output=True, text=True, timeout=10, cwd=str(cwd),
        )
        if result.returncode == 0 and result.stdout:
            consecutive = max_consecutive = 0
            for line in result.stdout.splitlines():
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
        pass

    # Check 3: Security scan (bandit — staged files only)
    try:
        if shutil.which("bandit"):
            result_diff = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                capture_output=True, text=True, timeout=10, cwd=str(cwd),
            )
            staged_py = []
            if result_diff.returncode == 0:
                staged_py = [
                    str(cwd / f) for f in result_diff.stdout.splitlines()
                    if f.endswith(".py") and not any(part in Path(f).parts for part in ("venv", ".venv", "node_modules", "__pycache__"))
                ]
            if staged_py:
                result = subprocess.run(
                    ["bandit", "-q", "-ll", "-x", ".venv,venv"] + staged_py,
                    capture_output=True, text=True, timeout=30, cwd=str(cwd),
                )
                if result.returncode != 0 and result.stdout.strip():
                    issue_count = result.stdout.count("Issue:")
                    if issue_count > 0:
                        warnings.append(f"security: bandit found {issue_count} issue(s)")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    count = len(warnings)
    if count > 0:
        print(f"Quality gate: {count} warning(s)", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)
    else:
        print("Quality gate: 0 warnings", file=sys.stderr)


# ── Core safety evaluation ──────────────────────────────────────────────────

def _is_safe_for_confirmation_wrapper(command: str) -> bool:
    return not _DANGEROUS_COMPOUND_RE.search(command)


def evaluate(command: str) -> int:
    """Run regex evaluation. Returns 0 (allow) or 2 (block)."""
    cmd = normalize_command(command)
    for pattern, message in COMPILED_BLOCKS:
        if pattern.search(cmd):
            print(f"[zie-framework] BLOCKED: {message}")
            return 2
    for pattern, message in COMPILED_WARNS:
        if pattern.search(cmd):
            print(f"[zie-framework] WARNING: {message}")
    return 0


# ── Outer guard ──────────────────────────────────────────────────────────────
try:
    event = read_event()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    if tool_name not in {"Write", "Edit", "Bash"}:
        sys.exit(0)
except Exception:
    sys.exit(0)

cwd = get_cwd()

# ── Write / Edit — reviewer gate first, then relative path resolution ──────
if tool_name in {"Write", "Edit"}:
    # Reviewer gate: block self-approval of specs/plans
    gate_result = _check_reviewer_gate(tool_name, tool_input, cwd)
    if gate_result == 2:
        sys.exit(2)

    # Relative path resolution
    try:
        file_path = tool_input.get("file_path", "")
        if not file_path:
            sys.exit(0)
        p = Path(file_path)
        if p.is_absolute():
            sys.exit(0)
        cwd_resolved = cwd.resolve()
        abs_path = (cwd_resolved / p).resolve()
        if not abs_path.is_relative_to(cwd_resolved):
            print(
                f"[zie-framework] safety-check: relative path escapes cwd, skipping rewrite: {file_path}",
                file=sys.stderr,
            )
            sys.exit(0)
        updated = dict(tool_input)
        updated["file_path"] = str(abs_path)
        print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
        sys.exit(0)
    except Exception as e:
        print(f"[zie-framework] safety-check: {e}", file=sys.stderr)
        sys.exit(0)

# ── Bash — quality gate, then safety evaluate, then confirm-wrap ────────────
if tool_name == "Bash":
    try:
        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)
    except Exception:
        sys.exit(0)

    # Quality gate (warn-only, never blocks)
    try:
        _run_quality_gate(command, cwd)
    except Exception as e:
        log_error("safety-check", "quality_gate", e)

    config = load_config(cwd)
    mode = config.get("safety_check_mode")

    if mode == "agent":
        result = safety_check_agent.evaluate(command, mode, config.get("safety_agent_timeout_s"))
        sys.exit(result)

    result = evaluate(command)

    if mode == "both":
        try:
            log_path = project_tmp_path("safety-ab", cwd.name)
            record = {
                "ts": time.time(),
                "command": command,
                "agent": "regex",
                "agent_reason": "blocked" if result == 2 else "allowed",
            }
            with open(log_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[zie-framework] safety-check: A/B log write failed: {e}", file=sys.stderr)

    if result == 2:
        sys.exit(2)

    # ── Bash confirm-wrap sanitizer ───────────────────────────────────────
    try:
        if "Would run:" in command:
            sys.exit(0)
        normalized = re.sub(r"\s+", " ", command.strip())
        for pattern in CONFIRM_PATTERNS:
            if re.search(pattern, normalized):
                if not _is_safe_for_confirmation_wrapper(command):
                    print(
                        "[zie-framework] safety-check: compound command skipped confirmation wrap",
                        file=sys.stderr,
                    )
                    sys.exit(0)
                rewritten = (
                    f'printf "Would run: %s\\n" {shlex.quote(command)} '
                    f'&& read -p "Confirm? [y/N] " _y '
                    f'&& [ "$_y" = "y" ] && {{ {command}; }}'
                )
                updated = dict(tool_input)
                updated["command"] = rewritten
                print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
                sys.exit(0)
    except Exception as e:
        print(f"[zie-framework] safety-check: {e}", file=sys.stderr)
        sys.exit(0)