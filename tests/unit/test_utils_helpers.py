"""Tests for is_zie_initialized() and get_project_name() in utils.py."""
import os
import sys
from pathlib import Path

import pytest

HOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "hooks"))
sys.path.insert(0, HOOKS_DIR)

from utils import get_project_name, is_zie_initialized


class TestIsZieInitialized:
    def test_returns_true_when_zie_framework_dir_exists(self, tmp_path):
        (tmp_path / "zie-framework").mkdir()
        assert is_zie_initialized(tmp_path) is True

    def test_returns_false_when_zie_framework_dir_missing(self, tmp_path):
        assert is_zie_initialized(tmp_path) is False

    def test_returns_false_for_file_named_zie_framework(self, tmp_path):
        (tmp_path / "zie-framework").write_text("not a dir")
        assert is_zie_initialized(tmp_path) is False

    def test_accepts_path_object(self, tmp_path):
        (tmp_path / "zie-framework").mkdir()
        assert is_zie_initialized(Path(tmp_path)) is True


class TestGetProjectName:
    def test_returns_sanitized_name(self, tmp_path):
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        name = get_project_name(project_dir)
        assert name == "my-project"

    def test_sanitizes_special_chars(self, tmp_path):
        project_dir = tmp_path / "project with spaces"
        project_dir.mkdir()
        name = get_project_name(project_dir)
        assert " " not in name

    def test_nonempty_for_valid_dir(self, tmp_path):
        assert get_project_name(tmp_path) != ""
