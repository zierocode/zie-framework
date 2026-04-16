#!/usr/bin/env python3
"""Skill auto-injection: inject SKILL.md content based on SDLC stage."""

from __future__ import annotations

import json
from pathlib import Path

from utils_error import log_error

DEFAULT_SKILL_MAPPING: dict = {
    "spec": "spec-review",
    "plan": "write-plan",
    "implement": "impl-review",
}

MAX_INJECT_CHARS: int = 2000


def inject_skill_context(stage: str, cwd: Path) -> str | None:
    """Read SKILL.md for the given stage and return its content.

    Returns None if:
    - skill_auto_inject is disabled in .config
    - stage is not in the mapping
    - SKILL.md file is missing
    - project has no zie-framework/ directory

    Content is truncated to MAX_INJECT_CHARS characters.
    """
    config_path = cwd / "zie-framework" / ".config"
    if not config_path.exists():
        return None

    try:
        config = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        log_error("utils_skill_inject", "read_config", e)
        return None

    # Check enabled flag (default: true)
    auto_config = config.get("skill_auto_inject", {})
    if isinstance(auto_config, dict) and not auto_config.get("enabled", True):
        return None

    # Resolve mapping: user config overrides default
    mapping = (
        auto_config.get("mapping", DEFAULT_SKILL_MAPPING) if isinstance(auto_config, dict) else DEFAULT_SKILL_MAPPING
    )
    skill_name = mapping.get(stage)
    if not skill_name:
        return None

    # Read SKILL.md
    skill_path = cwd / "skills" / skill_name / "SKILL.md"
    # Also check plugin directory (for installed plugins)
    if not skill_path.exists():
        skill_path = cwd / ".claude-plugin" / "skills" / skill_name / "SKILL.md"

    if not skill_path.exists():
        return None

    try:
        content = skill_path.read_text()
        if len(content) > MAX_INJECT_CHARS:
            content = content[:MAX_INJECT_CHARS].rstrip() + "\n[...truncated]"
        return content
    except OSError as e:
        log_error("utils_skill_inject", "read_skill_file", e)
        return None
