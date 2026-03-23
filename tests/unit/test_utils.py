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


class TestAtomicWrite:
    def test_writes_content_to_target(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "pending_learn.txt"
        atomic_write(target, "project=foo\nwip=bar\n")
        assert target.read_text() == "project=foo\nwip=bar\n"

    def test_no_tmp_file_left_on_success(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "pending_learn.txt"
        atomic_write(target, "hello")
        tmp_file = target.with_suffix(".tmp")
        assert not tmp_file.exists(), ".tmp file must be cleaned up after successful rename"

    def test_overwrites_existing_file(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "pending_learn.txt"
        target.write_text("old content")
        atomic_write(target, "new content")
        assert target.read_text() == "new content"

    def test_handles_empty_content(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "out.txt"
        atomic_write(target, "")
        assert target.read_text() == ""

    def test_stale_tmp_overwritten(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "out.txt"
        stale_tmp = target.with_suffix(".tmp")
        stale_tmp.write_text("stale")
        atomic_write(target, "fresh")
        assert target.read_text() == "fresh"
        assert not stale_tmp.exists()


class TestSafeProjectName:
    def test_alphanumeric_unchanged(self):
        from utils import safe_project_name
        assert safe_project_name("myproject") == "myproject"

    def test_spaces_replaced_with_dash(self):
        from utils import safe_project_name
        assert safe_project_name("my project") == "my-project"

    def test_special_chars_replaced(self):
        from utils import safe_project_name
        assert safe_project_name("my project!") == "my-project-"

    def test_empty_string_returns_empty(self):
        from utils import safe_project_name
        assert safe_project_name("") == ""

    def test_already_safe_no_change(self):
        from utils import safe_project_name
        assert safe_project_name("zie-framework") == "zie-framework"

    def test_project_tmp_path_uses_safe_project_name(self):
        """project_tmp_path output must equal /tmp/zie-{safe_project_name(p)}-{name}."""
        from utils import safe_project_name
        from pathlib import Path
        p = "my project!"
        expected = Path(f"/tmp/zie-{safe_project_name(p)}-last-test")
        assert project_tmp_path("last-test", p) == expected


class TestCallZieMemoryApi:
    def test_raises_on_unreachable_url(self):
        from utils import call_zie_memory_api
        with pytest.raises(Exception):
            call_zie_memory_api(
                "https://localhost:19999", "fake-key",
                "/api/hooks/session-stop", {"project": "test"}, timeout=1,
            )

    def test_raises_type_error_on_non_serializable_payload(self):
        from utils import call_zie_memory_api
        with pytest.raises((TypeError, Exception)):
            call_zie_memory_api(
                "https://localhost:19999", "fake-key",
                "/api/hooks/session-stop", {"bad": object()},
            )

    def test_constructs_correct_request(self):
        from utils import call_zie_memory_api
        from unittest import mock
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.method
            captured["auth"] = req.get_header("Authorization")
            captured["content_type"] = req.get_header("Content-type")
            captured["timeout"] = timeout

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            call_zie_memory_api(
                "https://zie-memory.example.com", "my-key",
                "/api/hooks/session-stop", {"project": "test"},
            )

        assert captured["url"] == "https://zie-memory.example.com/api/hooks/session-stop"
        assert captured["method"] == "POST"
        assert captured["auth"] == "Bearer my-key"
        assert captured["content_type"] == "application/json"

    def test_default_timeout_is_5(self):
        from utils import call_zie_memory_api
        from unittest import mock
        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["timeout"] = timeout

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            call_zie_memory_api(
                "https://zie-memory.example.com", "my-key",
                "/api/hooks/session-stop", {"project": "test"},
            )

        assert captured["timeout"] == 5


class TestSafeWriteTmp:
    def test_normal_write_returns_true(self, tmp_path):
        from utils import safe_write_tmp
        target = tmp_path / "zie-test-foo"
        result = safe_write_tmp(target, "hello")
        assert result is True
        assert target.read_text() == "hello"

    def test_normal_write_is_atomic(self, tmp_path):
        """Content is written via a .tmp sibling then renamed."""
        from utils import safe_write_tmp
        target = tmp_path / "zie-test-atomic"
        safe_write_tmp(target, "data")
        tmp_sibling = tmp_path / "zie-test-atomic.tmp"
        assert not tmp_sibling.exists()
        assert target.read_text() == "data"

    def test_symlink_returns_false(self, tmp_path):
        from utils import safe_write_tmp
        real_file = tmp_path / "real.txt"
        real_file.write_text("secret")
        link = tmp_path / "zie-test-link"
        link.symlink_to(real_file)
        result = safe_write_tmp(link, "overwrite")
        assert result is False
        assert real_file.read_text() == "secret"

    def test_symlink_to_nonexistent_returns_false(self, tmp_path):
        from utils import safe_write_tmp
        link = tmp_path / "zie-test-dangling"
        link.symlink_to(tmp_path / "does-not-exist")
        result = safe_write_tmp(link, "data")
        assert result is False

    def test_symlink_blocked_emits_stderr_warning(self, tmp_path, capsys):
        from utils import safe_write_tmp
        link = tmp_path / "zie-test-warn"
        link.symlink_to(tmp_path / "anything")
        safe_write_tmp(link, "x")
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "symlink" in captured.err.lower()

    def test_oserror_returns_false(self, tmp_path):
        from utils import safe_write_tmp
        from unittest import mock
        target = tmp_path / "zie-test-err"
        with mock.patch("os.replace", side_effect=OSError("disk full")):
            result = safe_write_tmp(target, "data")
        assert result is False

    def test_path_not_exist_is_normal_write(self, tmp_path):
        from utils import safe_write_tmp
        target = tmp_path / "zie-test-new"
        assert not target.exists()
        result = safe_write_tmp(target, "first-run")
        assert result is True
        assert target.read_text() == "first-run"
