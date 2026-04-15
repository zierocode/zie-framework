#!/usr/bin/env python3
"""zie-context-loader — Scan commands/skills, build command map, cache per session."""

import os
import sys
from pathlib import Path


def build_context_map(cwd: Path) -> dict:
    """Scan commands/ and skills/, return {commands: [{name, file, path}], skills: [{name, path}]}."""
    commands = []
    skills = []

    # Scan commands/*.md
    commands_dir = cwd / "commands"
    if commands_dir.exists():
        for f in commands_dir.glob("*.md"):
            commands.append({
                "name": f"/{f.stem}",
                "file": f.name,
                "path": str(f.relative_to(cwd))
            })

    # Scan skills/*/SKILL.md
    skills_dir = cwd / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skills.append({
                        "name": skill_dir.name,
                        "path": str(skill_file.relative_to(cwd))
                    })

    return {"commands": commands, "skills": skills}


def _get_skill_mtime(cwd: Path) -> float:
    """Get SKILL.md mtime for cache invalidation."""
    skill_path = cwd / "skills" / "context-map" / "SKILL.md"
    if skill_path.exists():
        return skill_path.stat().st_mtime
    return 0.0


def _build_cache_key(skill_mtime: float) -> str:
    """Build session-scoped cache key with mtime-gate."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return f"session:{session_id}:command_map:{skill_mtime}"


def get_cached_context(cwd: Path) -> dict:
    """Get command map from session cache, or build if missing."""
    try:
        from utils_cache import get_cache_manager
        skill_mtime = _get_skill_mtime(cwd)
        cache_key = _build_cache_key(skill_mtime)
        session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
        cache = get_cache_manager(cwd)
        return cache.get_or_compute(
            cache_key, session_id, lambda: build_context_map(cwd), ttl=1800
        )
    except Exception as e:
        print(f"[zie-framework] context-loader: cache failed: {e}", file=sys.stderr)
        return build_context_map(cwd)


if __name__ == "__main__":
    try:
        context = build_context_map(Path.cwd())
        print(f"Commands: {len(context['commands'])}")
        print(f"Skills: {len(context['skills'])}")
        sys.exit(0)
    except Exception:
        sys.exit(0)
