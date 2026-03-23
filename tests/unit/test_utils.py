"""Tests for hooks/utils.py"""
import os
import sys
from pathlib import Path
import pytest

# Add hooks/ to path so we can import utils directly
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from utils import parse_roadmap_now, project_tmp_path


class TestParseRoadmapNow:
    def test_missing_file_returns_empty(self, tmp_path):
        result = parse_roadmap_now(tmp_path / "nonexistent.md")
        assert result == []

    def test_no_now_header_returns_empty(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Done\n- [x] something\n")
        assert parse_roadmap_now(f) == []

    def test_empty_now_section_returns_empty(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n\n## Next\n- [ ] foo\n")
        assert parse_roadmap_now(f) == []

    def test_items_returned_from_now(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] feature one\n- [x] feature two\n## Next\n- [ ] other\n")
        result = parse_roadmap_now(f)
        assert result == ["feature one", "feature two"]

    def test_markdown_links_stripped(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] my feature — [plan](plans/foo.md)\n")
        result = parse_roadmap_now(f)
        assert result == ["my feature — plan"]

    def test_stops_at_next_header(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] item1\n## Ready\n- [ ] item2\n")
        result = parse_roadmap_now(f)
        assert result == ["item1"]

    def test_accepts_string_path(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] item\n")
        result = parse_roadmap_now(str(f))
        assert result == ["item"]


class TestProjectTmpPath:
    def test_basic_name(self):
        result = project_tmp_path("last-test", "my-project")
        assert result == Path("/tmp/zie-my-project-last-test")

    def test_spaces_replaced(self):
        result = project_tmp_path("edit-count", "my project!")
        assert str(result) == "/tmp/zie-my-project--edit-count"

    def test_case_preserved(self):
        result = project_tmp_path("x", "ABC")
        assert result == Path("/tmp/zie-ABC-x")

    def test_returns_path_object(self):
        result = project_tmp_path("foo", "bar")
        assert isinstance(result, Path)
