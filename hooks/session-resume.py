#!/usr/bin/env python3
"""SessionStart hook — inject current SDLC state for instant session orientation."""
import os
import subprocess
import sys
import time as _time
from pathlib import Path

_hook_start = _time.monotonic()

sys.path.insert(0, os.path.dirname(__file__))
from utils import get_cwd, load_config, log_hook_timing, parse_roadmap_now, read_event  # noqa: E402

PLAYWRIGHT_MIN_VERSION = (1, 55, 1)


def _check_playwright_version(config: dict) -> None:
    """Warn and disable playwright_enabled if installed version is below minimum safe."""
    if not config.get("playwright_enabled"):
        return

    raw = ""
    try:
        result = subprocess.run(
            ["playwright", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        raw = result.stdout.strip()
        parts = raw.split()
        version_str = parts[-1] if parts else ""
        version_tuple = tuple(int(x) for x in version_str.split(".") if x)
        if not version_tuple:
            raise ValueError("empty version")
        if version_tuple < PLAYWRIGHT_MIN_VERSION:
            min_str = ".".join(str(x) for x in PLAYWRIGHT_MIN_VERSION)
            print(
                f"[zie-framework] WARNING: Playwright {version_str} is below minimum safe"
                f" version {min_str} (CVE-2025-59288). playwright_enabled disabled for this"
                f" session. Run: playwright self-update",
                file=sys.stderr,
            )
            config["playwright_enabled"] = False
    except (FileNotFoundError, OSError):
        print(
            "[zie-framework] WARNING: playwright not found."
            " playwright_enabled disabled for this session.",
            file=sys.stderr,
        )
        config["playwright_enabled"] = False
    except ValueError:
        print(
            f"[zie-framework] session-resume: could not parse playwright version from: \"{raw}\"",
            file=sys.stderr,
        )
    except Exception as e:
        print(
            f"[zie-framework] session-resume: playwright version check failed: {e}",
            file=sys.stderr,
        )


# Outer guard — any unhandled exception exits 0 (never blocks Claude)
try:
    event = read_event()

    cwd = get_cwd()
    zf = cwd / "zie-framework"

    if not zf.exists():
        sys.exit(0)

    # Read config
    config = load_config(cwd)

    # Playwright version safety check (CVE-2025-59288)
    _check_playwright_version(config)

    roadmap_file = zf / "ROADMAP.md"
    now_items = parse_roadmap_now(roadmap_file)

    # Read VERSION
    version = "?"
    version_file = cwd / "VERSION"
    if version_file.exists():
        version = version_file.read_text().strip()

    project_name = cwd.name
    project_type = config.get("project_type")
    zie_memory = config.get("zie_memory_enabled")

    # Write config vars to CLAUDE_ENV_FILE (SessionStart env injection)
    _env_file_path = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if _env_file_path:
        try:
            _debounce_ms = "3000"
            try:
                _debounce_ms = str(int(config.get("auto_test_debounce_ms")))
            except (TypeError, ValueError):
                _debounce_ms = "3000"
            _env_lines = (
                f"export ZIE_PROJECT='{project_name}'\n"
                f"export ZIE_TEST_RUNNER='{config.get('test_runner')}'\n"
                f"export ZIE_MEMORY_ENABLED='{'1' if zie_memory else '0'}'\n"
                f"export ZIE_AUTO_TEST_DEBOUNCE_MS='{_debounce_ms}'\n"
            )
            _p = Path(_env_file_path)
            if os.path.islink(_p):
                print(
                    f"[zie-framework] WARNING: CLAUDE_ENV_FILE is a symlink,"
                    f" skipping write: {_p}",
                    file=sys.stderr,
                )
            else:
                _p.write_text(_env_lines)
                os.chmod(_p, 0o600)
        except Exception as e:
            print(
                f"[zie-framework] session-resume: env-file write failed: {e}",
                file=sys.stderr,
            )

    # Active feature: first Now item, or fallback message
    if now_items:
        active_label = now_items[0]
    else:
        active_label = "No active feature — run /zie-backlog to start one"

    lines = [
        f"[zie-framework] {project_name} ({project_type}) v{version}",
        f"  Active: {active_label}",
        f"  Brain: {'enabled' if zie_memory else 'disabled'}",
        "  → Run /zie-status for full state",
    ]

    print("\n".join(lines))

    # Drift detection — call knowledge-hash.py --check
    try:
        import subprocess as _sp
        _kh_script = os.environ.get(
            "ZIE_KNOWLEDGE_HASH_SCRIPT",
            os.path.join(os.path.dirname(__file__), "knowledge-hash.py"),
        )
        _result = _sp.run(
            [sys.executable, _kh_script, "--check", "--root", str(cwd)],
            capture_output=True, text=True, timeout=10,
        )
        if _result.stdout.strip():
            print(_result.stdout.strip())
    except Exception as e:
        print(f"[zie-framework] session-resume: drift check failed: {e}", file=sys.stderr)

except Exception:
    sys.exit(0)

log_hook_timing(
    "session-resume",
    int((_time.monotonic() - _hook_start) * 1000),
    0,
    session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
)
