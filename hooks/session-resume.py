#!/usr/bin/env python3
"""SessionStart hook — inject current SDLC state for instant session orientation."""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import get_cwd, load_config, parse_roadmap_now, read_event

event = read_event()

cwd = get_cwd()
zf = cwd / "zie-framework"

if not zf.exists():
    sys.exit(0)

# Read config
config = load_config(cwd)

roadmap_file = zf / "ROADMAP.md"
now_items = parse_roadmap_now(roadmap_file)

# Read VERSION
version = "?"
version_file = cwd / "VERSION"
if version_file.exists():
    version = version_file.read_text().strip()

project_name = cwd.name
project_type = config.get("project_type", "unknown")
zie_memory = config.get("zie_memory_enabled", False)

# Write config vars to CLAUDE_ENV_FILE (SessionStart env injection)
_env_file_path = os.environ.get("CLAUDE_ENV_FILE", "").strip()
if _env_file_path:
    try:
        _debounce_ms = "3000"
        try:
            _debounce_ms = str(int(config.get("auto_test_debounce_ms", 3000)))
        except (TypeError, ValueError):
            _debounce_ms = "3000"
        _env_lines = (
            f"export ZIE_PROJECT='{project_name}'\n"
            f"export ZIE_TEST_RUNNER='{config.get('test_runner', '')}'\n"
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
