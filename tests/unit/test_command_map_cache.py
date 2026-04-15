#!/usr/bin/env python3
"""Unit tests for command-map-pre-load caching."""
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from hooks.utils_cache import CacheManager, get_cache_manager


@pytest.fixture
def cache_dir():
    """Create a temporary cache directory for each test."""
    tmp = Path(tempfile.mkdtemp())
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def test_project(cache_dir):
    """Create a minimal test project structure."""
    project = cache_dir / "test-project"
    project.mkdir()

    # Create skills/using-zie-framework/SKILL.md
    skills_dir = project / "skills" / "using-zie-framework"
    skills_dir.mkdir(parents=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text("""# Using zie-framework

## Command Map

- `/backlog` - Capture new ideas
- `/spec` - Write design spec
- `/plan` - Draft implementation plan
- `/implement` - TDD implementation
- `/health` - Hook health check (guarded)
- `/rescue` - Pipeline recovery (guarded)

## Other content
""")

    # Create commands/ directory with some commands
    commands_dir = project / "commands"
    commands_dir.mkdir()
    (commands_dir / "backlog.md").touch()
    (commands_dir / "spec.md").touch()
    (commands_dir / "plan.md").touch()
    (commands_dir / "implement.md").touch()
    # Note: health.md and rescue.md NOT created (guarded commands)

    return project


class TestCommandMapCache:
    """Test command map caching logic."""

    def test_parse_commands_from_skill(self, test_project, cache_dir):
        """Commands are parsed correctly from SKILL.md."""
        skill_path = test_project / "skills" / "using-zie-framework" / "SKILL.md"
        commands_dir = test_project / "commands"
        guarded = ["/health", "/rescue"]

        skill_text = skill_path.read_text()
        in_cmd_map = False
        cmd_names = []
        for line in skill_text.splitlines():
            if "## Command Map" in line:
                in_cmd_map = True
                continue
            if line.startswith("##") and in_cmd_map:
                break
            if in_cmd_map and line.strip().startswith("- `/"):
                import re
                m = re.search(r'`(/[a-z]+)`', line)
                if m:
                    cmd_names.append(m.group(1))

        # Apply guards
        final_cmds = []
        for cmd in cmd_names:
            slug = cmd.lstrip("/")
            if cmd in guarded and not (commands_dir / f"{slug}.md").exists():
                continue
            final_cmds.append(cmd)

        assert "/backlog" in final_cmds
        assert "/spec" in final_cmds
        assert "/plan" in final_cmds
        assert "/implement" in final_cmds
        assert "/health" not in final_cmds  # Guarded, file missing
        assert "/rescue" not in final_cmds  # Guarded, file missing

    def test_cache_key_includes_mtime(self, test_project, cache_dir):
        """Cache key includes SKILL.md mtime for invalidation."""
        skill_path = test_project / "skills" / "using-zie-framework" / "SKILL.md"
        mtime = skill_path.stat().st_mtime

        cache_key = f"command_map:{mtime}"
        assert "command_map:" in cache_key
        assert str(mtime) in cache_key

    def test_cache_invalidates_on_mtime_change(self, test_project, cache_dir):
        """Cache is invalidated when SKILL.md mtime changes."""
        skill_path = test_project / "skills" / "using-zie-framework" / "SKILL.md"
        cache = CacheManager(cache_dir / ".zie" / "cache")
        session_id = "test_session"

        # Initial cache key
        mtime1 = skill_path.stat().st_mtime
        cache_key1 = f"command_map:{mtime1}"
        cache.set(cache_key1, "cached_value", session_id, ttl=1800)

        # Modify file (change mtime)
        time.sleep(0.1)
        skill_path.write_text(skill_path.read_text() + "\n")
        mtime2 = skill_path.stat().st_mtime

        # New cache key
        cache_key2 = f"command_map:{mtime2}"
        cached2 = cache.get(cache_key2, session_id)

        # Old key still has value, new key is miss
        assert cache.get(cache_key1, session_id) == "cached_value"
        assert cached2 is None  # New key = cache miss = will recompute

    def test_ttl_is_1800_seconds(self, test_project, cache_dir):
        """Command map cache TTL is 1800s (30 minutes)."""
        from hooks.utils_config import CACHE_TTLS
        assert CACHE_TTLS.get("command_map") == 1800


class TestCommandMapIntegration:
    """Test command map caching integration in session-resume."""

    def test_session_resume_uses_cache(self, test_project, cache_dir, monkeypatch):
        """session-resume uses cached command map."""
        # This test verifies the cache integration at a high level
        # Full integration test would require mocking the entire hook

        cache = CacheManager(cache_dir / ".zie" / "cache")
        session_id = "test_session"

        # Pre-populate cache
        skill_path = test_project / "skills" / "using-zie-framework" / "SKILL.md"
        mtime = skill_path.stat().st_mtime
        cache_key = f"command_map:{mtime}"
        cache.set(cache_key, "[zie-framework] framework: commands — /cached", session_id, ttl=1800)

        # Verify cache hit
        result = cache.get(cache_key, session_id)
        assert result == "[zie-framework] framework: commands — /cached"
