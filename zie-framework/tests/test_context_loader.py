#!/usr/bin/env python3
"""Unit tests for hooks/zie-context-loader.py."""

import pytest
from pathlib import Path
import tempfile
import os


class TestBuildContextMap:
    """Tests for build_context_map() function."""

    def test_build_context_map_returns_dict(self):
        """build_context_map should return a dict with 'commands' and 'skills' keys."""
        from hooks.zie_context_loader import build_context_map
        result = build_context_map(Path.cwd())
        assert isinstance(result, dict)
        assert "commands" in result
        assert "skills" in result
        assert isinstance(result["commands"], list)
        assert isinstance(result["skills"], list)

    def test_missing_zie_framework_returns_empty(self):
        """build_context_map should return empty lists when commands/ don't exist."""
        from hooks.zie_context_loader import build_context_map
        with tempfile.TemporaryDirectory() as tmp:
            result = build_context_map(Path(tmp))
            assert result == {"commands": [], "skills": []}

    def test_scan_commands_md_files(self):
        """build_context_map should scan commands/*.md files."""
        from hooks.zie_context_loader import build_context_map
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            commands_dir = tmp_path / "commands"
            commands_dir.mkdir()
            (commands_dir / "backlog.md").write_text("# backlog")
            (commands_dir / "spec.md").write_text("# spec")

            result = build_context_map(tmp_path)
            assert len(result["commands"]) == 2
            command_names = [c["name"] for c in result["commands"]]
            assert "/backlog" in command_names
            assert "/spec" in command_names

    def test_scan_skills_skill_md_files(self):
        """build_context_map should scan skills/*/SKILL.md files."""
        from hooks.zie_context_loader import build_context_map
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skills_dir = tmp_path / "skills"
            skills_dir.mkdir()
            skill_dir = skills_dir / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# test skill")

            result = build_context_map(tmp_path)
            assert len(result["skills"]) == 1
            assert result["skills"][0]["name"] == "test-skill"
            assert "SKILL.md" in result["skills"][0]["path"]


class TestCacheKey:
    """Tests for cache key building."""

    def test_cache_key_includes_session_id(self):
        """Cache key should include session ID from environment."""
        from hooks.zie_context_loader import _build_cache_key
        os.environ["CLAUDE_SESSION_ID"] = "test-123"
        key = _build_cache_key(1234567890.0)
        assert "session:test-123" in key
        assert "command_map" in key
        assert "1234567890" in key

    def test_cache_key_default_session(self):
        """Cache key should use 'default' when CLAUDE_SESSION_ID not set."""
        from hooks.zie_context_loader import _build_cache_key
        if "CLAUDE_SESSION_ID" in os.environ:
            del os.environ["CLAUDE_SESSION_ID"]
        key = _build_cache_key(0.0)
        assert "session:default" in key


class TestGetSkillMtime:
    """Tests for _get_skill_mtime() function."""

    def test_get_skill_mtime_returns_float(self):
        """_get_skill_mtime should return a float timestamp."""
        from hooks.zie_context_loader import _get_skill_mtime
        result = _get_skill_mtime(Path.cwd())
        assert isinstance(result, float)

    def test_get_skill_mtime_missing_file(self):
        """_get_skill_mtime should return 0.0 when SKILL.md doesn't exist."""
        from hooks.zie_context_loader import _get_skill_mtime
        with tempfile.TemporaryDirectory() as tmp:
            result = _get_skill_mtime(Path(tmp))
            assert result == 0.0
