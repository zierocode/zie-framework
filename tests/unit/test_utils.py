"""Tests for hooks/utils.py"""
import os
import sys
import tempfile
import time
from pathlib import Path
import pytest

# Add hooks/ to path so we can import utils directly
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "hooks"))

import json
from unittest.mock import patch
from utils import parse_roadmap_now, project_tmp_path, read_event, get_cwd, parse_roadmap_section, get_cached_roadmap, write_roadmap_cache, validate_config, load_config


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
        expected = Path(tempfile.gettempdir()) / "zie-my-project-last-test"
        assert result == expected

    def test_spaces_replaced(self):
        result = project_tmp_path("edit-count", "my project!")
        expected = Path(tempfile.gettempdir()) / "zie-my-project--edit-count"
        assert result == expected

    def test_case_preserved(self):
        result = project_tmp_path("x", "ABC")
        expected = Path(tempfile.gettempdir()) / "zie-ABC-x"
        assert result == expected

    def test_returns_path_object(self):
        result = project_tmp_path("foo", "bar")
        assert isinstance(result, Path)


class TestAtomicWrite:
    def test_writes_content_to_target(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "pending_learn.txt"
        atomic_write(target, "project=foo\nwip=bar\n")
        assert target.read_text() == "project=foo\nwip=bar\n"

    def test_atomic_write_no_predictable_tmp_sibling(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "pending_learn.txt"
        atomic_write(target, "hello")
        assert not target.with_suffix(".tmp").exists(), (
            "atomic_write must not leave a predictable .tmp sibling"
        )

    def test_atomic_write_permissions(self, tmp_path):
        from utils import atomic_write
        target = tmp_path / "pending_learn.txt"
        atomic_write(target, "hello")
        mode = oct(os.stat(target).st_mode)[-3:]
        assert mode == "600", f"Expected 600 permissions, got {mode}"

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
        """project_tmp_path output must equal <tmpdir>/zie-{safe_project_name(p)}-{name}."""
        from utils import safe_project_name
        p = "my project!"
        expected = Path(tempfile.gettempdir()) / f"zie-{safe_project_name(p)}-last-test"
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


class TestGetPluginDataDir:
    def test_uses_claude_plugin_data_when_set(self, tmp_path, monkeypatch):
        from utils import get_plugin_data_dir
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        result = get_plugin_data_dir("my-project")
        assert str(result).startswith(str(tmp_path))

    def test_subdirectory_is_safe_project_name(self, tmp_path, monkeypatch):
        from utils import get_plugin_data_dir, safe_project_name
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        result = get_plugin_data_dir("my project!")
        assert result.name == safe_project_name("my project!")

    def test_directory_is_created(self, tmp_path, monkeypatch):
        from utils import get_plugin_data_dir
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        result = get_plugin_data_dir("newproject")
        assert result.is_dir()

    def test_fallback_to_tmp_when_env_unset(self, monkeypatch, capsys):
        from utils import get_plugin_data_dir, safe_project_name
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        result = get_plugin_data_dir("myproject")
        safe = safe_project_name("myproject")
        expected = Path(tempfile.gettempdir()) / f"zie-{safe}-persistent"
        assert result == expected

    def test_fallback_emits_stderr_warning(self, monkeypatch, capsys):
        from utils import get_plugin_data_dir
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        get_plugin_data_dir("myproject")
        captured = capsys.readouterr()
        assert "CLAUDE_PLUGIN_DATA" in captured.err
        assert "fallback" in captured.err.lower() or "/tmp" in captured.err

    def test_fallback_directory_is_created(self, monkeypatch):
        from utils import get_plugin_data_dir
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)
        result = get_plugin_data_dir("myproject")
        assert result.is_dir()

    def test_empty_env_var_treated_as_unset(self, monkeypatch, capsys):
        from utils import get_plugin_data_dir
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", "")
        result = get_plugin_data_dir("myproject")
        assert str(result).startswith(str(tempfile.gettempdir()))
        captured = capsys.readouterr()
        assert "CLAUDE_PLUGIN_DATA" in captured.err

    def test_returns_path_object(self, tmp_path, monkeypatch):
        from utils import get_plugin_data_dir
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        assert isinstance(get_plugin_data_dir("proj"), Path)

    def test_special_chars_in_project_name_sanitized(self, tmp_path, monkeypatch):
        from utils import get_plugin_data_dir
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        result = get_plugin_data_dir("my/evil/../project")
        # Path() must not escape tmp_path via traversal
        assert str(result).startswith(str(tmp_path))
        assert ".." not in str(result)


class TestSafeWritePersistent:
    def test_normal_write_returns_true(self, tmp_path):
        from utils import safe_write_persistent
        target = tmp_path / "data.txt"
        result = safe_write_persistent(target, "hello")
        assert result is True
        assert target.read_text() == "hello"

    def test_write_is_atomic_no_tmp_sibling(self, tmp_path):
        from utils import safe_write_persistent
        target = tmp_path / "data.txt"
        safe_write_persistent(target, "content")
        tmp_sibling = tmp_path / "data.txt.tmp"
        assert not tmp_sibling.exists()

    def test_symlink_returns_false(self, tmp_path):
        from utils import safe_write_persistent
        real = tmp_path / "real.txt"
        real.write_text("protected")
        link = tmp_path / "link.txt"
        link.symlink_to(real)
        result = safe_write_persistent(link, "attack")
        assert result is False
        assert real.read_text() == "protected"

    def test_symlink_emits_stderr_warning(self, tmp_path, capsys):
        from utils import safe_write_persistent
        link = tmp_path / "link.txt"
        link.symlink_to(tmp_path / "anything")
        safe_write_persistent(link, "x")
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "symlink" in captured.err.lower()

    def test_dangling_symlink_returns_false(self, tmp_path):
        from utils import safe_write_persistent
        link = tmp_path / "dangling.txt"
        link.symlink_to(tmp_path / "does-not-exist")
        result = safe_write_persistent(link, "data")
        assert result is False

    def test_oserror_returns_false(self, tmp_path):
        from utils import safe_write_persistent
        from unittest import mock
        target = tmp_path / "err.txt"
        with mock.patch("os.replace", side_effect=OSError("disk full")):
            result = safe_write_persistent(target, "data")
        assert result is False

    def test_overwrites_existing_content(self, tmp_path):
        from utils import safe_write_persistent
        target = tmp_path / "data.txt"
        target.write_text("old")
        safe_write_persistent(target, "new")
        assert target.read_text() == "new"

    def test_path_not_existing_is_normal_write(self, tmp_path):
        from utils import safe_write_persistent
        target = tmp_path / "new.txt"
        assert not target.exists()
        result = safe_write_persistent(target, "first")
        assert result is True
        assert target.read_text() == "first"

    def test_safe_write_persistent_permissions(self, tmp_path):
        from utils import safe_write_persistent
        target = tmp_path / "data.txt"
        safe_write_persistent(target, "data")
        mode = oct(os.stat(target).st_mode)[-3:]
        assert mode == "600", f"Expected 600 permissions, got {mode}"


class TestPersistentProjectPath:
    def test_returns_path_inside_plugin_data_dir(self, tmp_path, monkeypatch):
        from utils import persistent_project_path
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        result = persistent_project_path("edit-count", "myproject")
        assert result.parent.parent == tmp_path

    def test_filename_matches_name_arg(self, tmp_path, monkeypatch):
        from utils import persistent_project_path
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        result = persistent_project_path("pending_learn.txt", "myproject")
        assert result.name == "pending_learn.txt"

    def test_returns_path_object(self, tmp_path, monkeypatch):
        from utils import persistent_project_path
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        assert isinstance(persistent_project_path("x", "y"), Path)

    def test_mirrors_project_tmp_path_structure(self, tmp_path, monkeypatch):
        """persistent_project_path and project_tmp_path must use the same
        safe_project_name sanitization for the project segment."""
        from utils import persistent_project_path, safe_project_name
        monkeypatch.setenv("CLAUDE_PLUGIN_DATA", str(tmp_path))
        result = persistent_project_path("edit-count", "my project!")
        safe = safe_project_name("my project!")
        assert safe in str(result)


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

    def test_safe_write_tmp_permissions(self, tmp_path):
        from utils import safe_write_tmp
        target = tmp_path / "zie-test-perms"
        safe_write_tmp(target, "data")
        mode = oct(os.stat(target).st_mode)[-3:]
        assert mode == "600", f"Expected 600 permissions, got {mode}"


class TestProjectTmpPathEdgeCases:
    """Contract tests for project_tmp_path() with pathological project names.

    These tests document known behaviour (including known gaps like no length cap).
    If implementation changes, update assertions AND the spec.
    """

    def test_unicode_project_name(self):
        # Accented chars are outside [a-zA-Z0-9] — replaced with '-'
        result = project_tmp_path("last-test", "mon-projet-caf\u00e9")
        result_str = str(result)
        assert result_str.isascii(), f"Expected ASCII path, got: {result_str}"
        assert isinstance(result, Path)
        # 'é' → '-', so 'café' → 'caf-'
        expected = str(Path(tempfile.gettempdir()) / "zie-mon-projet-caf--last-test")
        assert result_str == expected

    def test_emoji_project_name(self):
        # Each emoji code point is non-alphanumeric — replaced with single '-'
        result = project_tmp_path("edit-count", "my-app-\U0001F680")
        result_str = str(result)
        assert result_str.isascii(), f"Expected ASCII path, got: {result_str}"
        assert isinstance(result, Path)
        # 'my-app-' + '🚀'→'-' → 'my-app--'; path = zie- + my-app-- + -edit-count
        expected = str(Path(tempfile.gettempdir()) / "zie-my-app---edit-count")
        assert result_str == expected

    def test_leading_dash_project_name(self):
        # '-' is not in [a-zA-Z0-9] but re.sub('-'→'-') is a no-op change
        result = project_tmp_path("last-test", "-myproject")
        expected = str(Path(tempfile.gettempdir()) / "zie--myproject-last-test")
        assert str(result) == expected
        assert isinstance(result, Path)

    def test_very_long_project_name(self):
        """No truncation: name >255 chars will cause OSError at write time, not at Path construction.

        This test documents the known gap — callers must handle OSError on write.
        """
        long_name = "x" * 256
        result = project_tmp_path("edit-count", long_name)
        assert isinstance(result, Path)
        assert len(result.name) > 255

    def test_path_traversal_attempt(self):
        # '.' and '/' are both outside [a-zA-Z0-9] — replaced with '-'
        # '../etc' → '---etc'
        result = project_tmp_path("last-test", "../etc")
        result_str = str(result)
        assert ".." not in result_str
        assert "tmp" in result_str.lower() or tempfile.gettempdir() in result_str
        expected = str(Path(tempfile.gettempdir()) / "zie----etc-last-test")
        assert result_str == expected

    def test_dot_only_project_name(self):
        # '.' → '-' via re.sub
        result = project_tmp_path("x", ".")
        result_str = str(result)
        expected = str(Path(tempfile.gettempdir()) / "zie---x")
        assert result_str == expected
        assert isinstance(result, Path)
        assert "/." not in result_str


class TestParseRoadmapNowEdgeCases:
    """Edge case tests for parse_roadmap_now().

    These tests document the parser's existing behaviour for inputs that are
    valid ROADMAP content but outside the basic happy path. They are
    contract tests — if behaviour changes, update the assertion AND the spec.
    """

    def test_bold_inline_markdown_in_task(self, tmp_path):
        # Bold markers are not in the link regex — they pass through unchanged
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] **Refactor** the payment module\n")
        result = parse_roadmap_now(f)
        assert result == ["**Refactor** the payment module"]

    def test_italic_inline_markdown_in_task(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] fix _memory leak_ in cache\n")
        result = parse_roadmap_now(f)
        assert result == ["fix _memory leak_ in cache"]

    def test_malformed_link_missing_closing_paren(self, tmp_path):
        # re.sub pattern requires closing ) — without it, the link is NOT stripped
        # Contract: raw text is preserved (no partial stripping)
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] my feature — [plan](plans/foo.md\n")
        result = parse_roadmap_now(f)
        assert result == ["my feature — [plan](plans/foo.md"]

    def test_html_entity_in_task_description(self, tmp_path):
        # HTML entities are never decoded — plain text passthrough
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] support &amp; operator\n")
        result = parse_roadmap_now(f)
        assert result == ["support &amp; operator"]

    def test_nested_bold_link_combo(self, tmp_path):
        # Link is stripped (well-formed), bold markers around link text are preserved
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] **bold link** — [spec](specs/foo.md)\n")
        result = parse_roadmap_now(f)
        assert result == ["**bold link** — spec"]


class TestParseRoadmapSection:
    def test_next_section_returns_items(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] a\n## Next\n- [ ] b\n- [ ] c\n## Done\n- [x] d\n")
        assert parse_roadmap_section(f, "next") == ["b", "c"]

    def test_done_section_returns_items(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Done\n- [x] finished task\n")
        assert parse_roadmap_section(f, "done") == ["finished task"]

    def test_case_insensitive_match(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## NEXT\n- [ ] item\n")
        assert parse_roadmap_section(f, "next") == ["item"]

    def test_missing_section_returns_empty(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] a\n")
        assert parse_roadmap_section(f, "done") == []

    def test_missing_file_returns_empty(self, tmp_path):
        assert parse_roadmap_section(tmp_path / "none.md", "next") == []

    def test_strips_markdown_links(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Next\n- [ ] my task — [plan](plans/foo.md)\n")
        assert parse_roadmap_section(f, "next") == ["my task — plan"]

    def test_parse_roadmap_now_still_works_via_wrapper(self, tmp_path):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] now item\n## Next\n- [ ] next item\n")
        assert parse_roadmap_now(f) == ["now item"]

    def test_parse_roadmap_section_delegates_to_content(self, tmp_path, monkeypatch):
        """parse_roadmap_section must call parse_roadmap_section_content, not re-implement."""
        import utils as utils_module
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Alpha\n- [ ] task one\n")
        calls = []
        original = utils_module.parse_roadmap_section_content
        def spy(content, section_name):
            calls.append((content, section_name))
            return original(content, section_name)
        monkeypatch.setattr(utils_module, "parse_roadmap_section_content", spy)
        result = parse_roadmap_section(f, "alpha")
        assert result == ["task one"]
        assert len(calls) == 1, "parse_roadmap_section must delegate to parse_roadmap_section_content"


class TestReadEvent:
    def test_valid_json_returns_dict(self):
        payload = json.dumps({"tool": "Write", "input": {}})
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = payload
            result = read_event()
        assert result == {"tool": "Write", "input": {}}

    def test_invalid_json_exits_zero(self):
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = "not-json"
            with pytest.raises(SystemExit) as exc:
                read_event()
        assert exc.value.code == 0

    def test_empty_stdin_exits_zero(self):
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = ""
            with pytest.raises(SystemExit) as exc:
                read_event()
        assert exc.value.code == 0


class TestLoadConfig:
    def test_returns_dict_for_valid_json_config(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text('{"safety_check_mode": "agent"}')
        from utils import load_config
        result = load_config(tmp_path)
        assert result.get("safety_check_mode") == "agent"

    def test_returns_defaults_when_no_config(self, tmp_path):
        from utils import load_config
        result = load_config(tmp_path)
        assert result["subprocess_timeout_s"] == 5

    def test_returns_defaults_on_invalid_json(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text("not valid json")
        from utils import load_config
        result = load_config(tmp_path)
        assert result["subprocess_timeout_s"] == 5

    def test_returns_defaults_on_empty_file(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text("")
        from utils import load_config
        result = load_config(tmp_path)
        assert result["subprocess_timeout_s"] == 5

    def test_boolean_value_preserved(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text('{"playwright_enabled": false, "has_frontend": true}')
        from utils import load_config
        result = load_config(tmp_path)
        assert result["playwright_enabled"] is False
        assert result["has_frontend"] is True

    def test_integer_value_preserved(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text('{"debounce_ms": 3000}')
        from utils import load_config
        result = load_config(tmp_path)
        assert result["debounce_ms"] == 3000

    def test_string_value_preserved(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text('{"test_runner": "pytest"}')
        from utils import load_config
        result = load_config(tmp_path)
        assert result["test_runner"] == "pytest"

class TestConfigTemplate:
    def test_template_contains_safety_check_mode(self):
        template = Path(REPO_ROOT) / "templates" / ".config.template"
        assert "safety_check_mode" in template.read_text(), (
            "templates/.config.template must contain safety_check_mode key"
        )

    def test_template_default_is_regex(self):
        template = Path(REPO_ROOT) / "templates" / ".config.template"
        content = template.read_text()
        # default must be "regex", not "agent" or "both"
        for line in content.splitlines():
            if "safety_check_mode" in line and "=" in line:
                _, _, val = line.partition("=")
                assert val.strip() == "regex", (
                    f"safety_check_mode default must be 'regex', got '{val.strip()}'"
                )


class TestGetCwd:
    def test_returns_claude_cwd_when_set(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_CWD", str(tmp_path))
        result = get_cwd()
        assert result == Path(str(tmp_path))

    def test_returns_getcwd_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("CLAUDE_CWD", raising=False)
        result = get_cwd()
        assert result == Path(os.getcwd())

    def test_returns_path_object(self, monkeypatch, tmp_path):
        monkeypatch.setenv("CLAUDE_CWD", str(tmp_path))
        assert isinstance(get_cwd(), Path)


class TestNormalizeCommand:
    @pytest.mark.parametrize("cmd,expected", [
        ("git   add  .", "git add ."),
        ("  GIT ADD .  ", "git add ."),
        ("git\t\tadd\t.", "git add ."),
        ("make\n test", "make test"),
        ("git add .", "git add ."),
        ("", ""),
        ("   ", ""),
        ("GIT PUSH ORIGIN MAIN", "git push origin main"),
    ])
    def test_normalize_command(self, cmd, expected):
        from utils import normalize_command
        assert normalize_command(cmd) == expected

    def test_lowercases_command(self):
        from utils import normalize_command
        result = normalize_command("MAKE TEST")
        assert result == "make test"

    def test_collapses_tabs_and_newlines(self):
        from utils import normalize_command
        result = normalize_command("git\t\tcommit\n-m\r\nmsg")
        assert result == "git commit -m msg"


class TestBlocksWarns:
    def test_blocks_importable_from_utils(self):
        from utils import BLOCKS
        assert isinstance(BLOCKS, list)
        assert len(BLOCKS) > 0

    def test_warns_importable_from_utils(self):
        from utils import WARNS
        assert isinstance(WARNS, list)
        assert len(WARNS) > 0

    def test_blocks_entries_are_tuples(self):
        from utils import BLOCKS
        for entry in BLOCKS:
            assert isinstance(entry, tuple)
            assert len(entry) == 2

    def test_warns_entries_are_tuples(self):
        from utils import WARNS
        for entry in WARNS:
            assert isinstance(entry, tuple)
            assert len(entry) == 2

    def test_blocks_contains_rm_rf_pattern(self):
        from utils import BLOCKS
        patterns = [p for p, _ in BLOCKS]
        assert any("rm" in p for p in patterns)

    def test_warns_contains_docker_compose_pattern(self):
        from utils import WARNS
        patterns = [p for p, _ in WARNS]
        assert any("docker" in p for p in patterns)


class TestSdlcStages:
    def test_sdlc_stages_is_exported(self):
        from utils import SDLC_STAGES
        assert SDLC_STAGES is not None

    def test_sdlc_stages_is_list(self):
        from utils import SDLC_STAGES
        assert isinstance(SDLC_STAGES, list)

    def test_sdlc_stages_contains_eight_entries(self):
        from utils import SDLC_STAGES
        assert len(SDLC_STAGES) == 8

    def test_sdlc_stages_values(self):
        from utils import SDLC_STAGES
        assert SDLC_STAGES == [
            "init", "backlog", "spec", "plan",
            "implement", "fix", "release", "retro",
        ]

    def test_sdlc_stages_all_strings(self):
        from utils import SDLC_STAGES
        assert all(isinstance(s, str) for s in SDLC_STAGES)

    def test_intent_sdlc_has_sdlc_stage_keywords(self):
        """intent-sdlc.py must cover key SDLC stage keywords."""
        content = (REPO_ROOT / "hooks" / "intent-sdlc.py").read_text()
        for keyword in ("implement", "fix", "release", "plan"):
            assert keyword in content, (
                f"intent-sdlc.py must reference SDLC stage keyword: {keyword}"
            )


class TestParseRoadmapNowWarnOnEmpty:
    def test_warn_false_default_no_stderr_when_empty(self, tmp_path, capsys):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n\n## Next\n- [ ] foo\n")
        result = parse_roadmap_now(f)
        assert result == []
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_warn_true_emits_stderr_when_now_empty(self, tmp_path, capsys):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n\n## Next\n- [ ] foo\n")
        result = parse_roadmap_now(f, warn_on_empty=True)
        assert result == []
        captured = capsys.readouterr()
        assert "[zie-framework]" in captured.err
        assert "Now section" in captured.err

    def test_warn_true_emits_stderr_when_now_absent(self, tmp_path, capsys):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Done\n- [x] something\n")
        result = parse_roadmap_now(f, warn_on_empty=True)
        assert result == []
        captured = capsys.readouterr()
        assert "[zie-framework]" in captured.err

    def test_warn_true_no_stderr_when_file_missing(self, tmp_path, capsys):
        result = parse_roadmap_now(tmp_path / "nonexistent.md", warn_on_empty=True)
        assert result == []
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_warn_true_no_stderr_when_now_has_items(self, tmp_path, capsys):
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n- [ ] active task\n")
        result = parse_roadmap_now(f, warn_on_empty=True)
        assert result == ["active task"]
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_existing_callers_unaffected(self, tmp_path, capsys):
        """Calling with no arguments must behave exactly as before."""
        f = tmp_path / "ROADMAP.md"
        f.write_text("## Now\n\n")
        result = parse_roadmap_now(f)
        assert result == []
        captured = capsys.readouterr()
        assert captured.err == ""


class TestRoadmapCache:
    """Tests for get_cached_roadmap() and write_roadmap_cache()."""

    # Use unique session IDs per test to avoid cross-test pollution in /tmp

    def test_get_returns_none_when_no_cache(self):
        """Cache miss returns None (no file written)."""
        result = get_cached_roadmap("test-sess-nocache-unique-99z", ttl=30)
        assert result is None

    def test_write_then_read_within_ttl(self):
        """Fresh cache returns written content."""
        sid = "test-sess-fresh-unique-99z"
        write_roadmap_cache(sid, "# ROADMAP\n## Now\n")
        result = get_cached_roadmap(sid, ttl=30)
        assert result == "# ROADMAP\n## Now\n"

    def test_get_returns_none_when_expired(self):
        """Stale cache (age >= ttl) returns None."""
        sid = "test-sess-stale-unique-99z"
        write_roadmap_cache(sid, "# ROADMAP\n")
        cache_file = Path(f"/tmp/zie-{sid}/roadmap.cache")
        old_time = time.time() - 60
        os.utime(cache_file, (old_time, old_time))
        result = get_cached_roadmap(sid, ttl=30)
        assert result is None

    def test_get_returns_none_on_bad_session_id(self):
        """Invalid/empty session ID returns None, does not raise."""
        result = get_cached_roadmap("", ttl=30)
        assert result is None

    def test_write_creates_parent_dirs(self):
        """write_roadmap_cache creates /tmp/zie-{session_id}/ if needed."""
        sid = "test-sess-newdir-unique-99z"
        cache_file = Path(f"/tmp/zie-{sid}/roadmap.cache")
        cache_file.unlink(missing_ok=True)
        write_roadmap_cache(sid, "content")
        assert cache_file.exists()
        assert cache_file.read_text() == "content"

    def test_write_silently_swallows_errors(self, monkeypatch):
        """write_roadmap_cache does not raise on I/O errors."""
        monkeypatch.setattr(Path, "mkdir", lambda *a, **kw: (_ for _ in ()).throw(OSError("no perms")))
        write_roadmap_cache("sess-err-unique-99z", "content")  # must not raise

    def test_cache_default_ttl_is_30(self):
        """Default TTL is 30 seconds."""
        sid = "test-sess-ttl-unique-99z"
        write_roadmap_cache(sid, "data")
        cache_file = Path(f"/tmp/zie-{sid}/roadmap.cache")
        # backdate by 29s — should still be fresh
        os.utime(cache_file, (time.time() - 29, time.time() - 29))
        assert get_cached_roadmap(sid) == "data"
        # backdate by 31s — should be stale
        os.utime(cache_file, (time.time() - 31, time.time() - 31))
        assert get_cached_roadmap(sid) is None


# ---------------------------------------------------------------------------
# TestGitStatusCache
# ---------------------------------------------------------------------------

from utils import get_cached_git_status, write_git_status_cache


class TestGitStatusCache:
    def test_cache_miss_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        result = get_cached_git_status("sid-git-001", "log", ttl=5)
        assert result is None

    def test_cache_hit_within_ttl(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        write_git_status_cache("sid-git-002", "log", "abc1234 some commit")
        result = get_cached_git_status("sid-git-002", "log", ttl=60)
        assert result == "abc1234 some commit"

    def test_cache_miss_after_ttl(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        write_git_status_cache("sid-git-003", "log", "old content")
        cache_file = tmp_path / "zie-sid-git-003" / "git-log.cache"
        old_mtime = time.time() - 10
        os.utime(cache_file, (old_mtime, old_mtime))
        result = get_cached_git_status("sid-git-003", "log", ttl=5)
        assert result is None

    def test_write_creates_parent_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        write_git_status_cache("sid-git-004", "branch", "main")
        assert (tmp_path / "zie-sid-git-004" / "git-branch.cache").exists()

    def test_different_keys_are_independent(self, tmp_path, monkeypatch):
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        write_git_status_cache("sid-git-005", "log", "log-data")
        write_git_status_cache("sid-git-005", "branch", "branch-data")
        assert get_cached_git_status("sid-git-005", "log", ttl=60) == "log-data"
        assert get_cached_git_status("sid-git-005", "branch", ttl=60) == "branch-data"

    def test_path_injection_sanitized(self, tmp_path, monkeypatch):
        """session_id with path separators must not escape tmp dir."""
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        write_git_status_cache("../../evil", "log", "data")
        # Must not write outside tmp_path
        for root, dirs, files in os.walk(str(tmp_path)):
            for f in files:
                full = os.path.join(root, f)
                assert full.startswith(str(tmp_path)), f"file escaped tmp: {full}"

    def test_key_injection_sanitized(self, tmp_path, monkeypatch):
        """cache key with path separators must not escape session dir."""
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        write_git_status_cache("sid-git-006", "../../evil", "data")
        for root, dirs, files in os.walk(str(tmp_path)):
            for f in files:
                full = os.path.join(root, f)
                assert full.startswith(str(tmp_path)), f"file escaped tmp: {full}"

    def test_read_error_returns_none(self, tmp_path, monkeypatch):
        """Unreadable cache dir returns None without raising."""
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        result = get_cached_git_status("nonexistent-sid-xyz", "log", ttl=60)
        assert result is None


class TestValidateConfig:
    def test_empty_dict_returns_all_defaults(self):
        result = validate_config({})
        assert result["subprocess_timeout_s"] == 5
        assert result["safety_agent_timeout_s"] == 30
        assert result["auto_test_max_wait_s"] == 15
        assert result["auto_test_timeout_ms"] == 30000

    def test_valid_values_preserved(self):
        result = validate_config({"subprocess_timeout_s": 10})
        assert result["subprocess_timeout_s"] == 10
        assert result["safety_agent_timeout_s"] == 30

    def test_wrong_type_replaced_with_default(self, capsys):
        result = validate_config({"subprocess_timeout_s": "fast"})
        assert result["subprocess_timeout_s"] == 5
        captured = capsys.readouterr()
        assert "defaulted keys" in captured.err
        assert "subprocess_timeout_s" in captured.err

    def test_warning_lists_all_defaulted_keys(self, capsys):
        validate_config({"subprocess_timeout_s": "x", "safety_agent_timeout_s": "y"})
        captured = capsys.readouterr()
        assert "subprocess_timeout_s" in captured.err
        assert "safety_agent_timeout_s" in captured.err

    def test_none_treated_as_empty_dict(self):
        result = validate_config(None)
        assert result["subprocess_timeout_s"] == 5

    def test_no_warning_on_full_valid_config(self, capsys):
        validate_config({
            "subprocess_timeout_s": 5,
            "safety_agent_timeout_s": 30,
            "auto_test_max_wait_s": 15,
            "auto_test_timeout_ms": 30000,
        })
        captured = capsys.readouterr()
        assert "defaulted" not in captured.err

    def test_no_warning_on_empty_dict(self, capsys):
        validate_config({})
        captured = capsys.readouterr()
        assert "defaulted" not in captured.err

    def test_load_config_returns_fully_typed_dict(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text('{"subprocess_timeout_s": 10}')
        result = load_config(tmp_path)
        assert result["safety_agent_timeout_s"] == 30
        assert result["subprocess_timeout_s"] == 10

    def test_load_config_missing_file_returns_defaults(self, tmp_path):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        result = load_config(tmp_path)
        assert result["subprocess_timeout_s"] == 5

    def test_load_config_json_array_returns_defaults(self, tmp_path, capsys):
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text('[1, 2, 3]')
        result = load_config(tmp_path)
        assert result["subprocess_timeout_s"] == 5
        captured = capsys.readouterr()
        assert "config parse error" in captured.err


class TestConfigDefaults:
    def test_config_defaults_has_all_required_keys(self):
        from utils import CONFIG_DEFAULTS
        required = {
            "safety_check_mode", "test_runner", "auto_test_debounce_ms",
            "auto_test_timeout_ms", "test_indicators", "project_type", "zie_memory_enabled",
        }
        assert required <= set(CONFIG_DEFAULTS.keys())

    def test_config_defaults_correct_types(self):
        from utils import CONFIG_DEFAULTS
        assert isinstance(CONFIG_DEFAULTS["safety_check_mode"], str)
        assert isinstance(CONFIG_DEFAULTS["test_runner"], str)
        assert isinstance(CONFIG_DEFAULTS["auto_test_debounce_ms"], int)
        assert isinstance(CONFIG_DEFAULTS["auto_test_timeout_ms"], int)
        assert isinstance(CONFIG_DEFAULTS["test_indicators"], str)
        assert isinstance(CONFIG_DEFAULTS["project_type"], str)
        assert isinstance(CONFIG_DEFAULTS["zie_memory_enabled"], bool)

    def test_load_config_includes_config_defaults_keys(self, tmp_path):
        from utils import load_config, CONFIG_DEFAULTS
        result = load_config(tmp_path)
        for key in CONFIG_DEFAULTS:
            assert key in result, f"load_config result must include CONFIG_DEFAULTS key: {key}"

    def test_loaded_values_override_defaults(self, tmp_path):
        from utils import load_config, CONFIG_DEFAULTS
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text('{"safety_check_mode": "agent", "auto_test_debounce_ms": 500}')
        result = load_config(tmp_path)
        assert result["safety_check_mode"] == "agent"
        assert result["auto_test_debounce_ms"] == 500
        assert result["test_runner"] == CONFIG_DEFAULTS["test_runner"]
        assert result["zie_memory_enabled"] == CONFIG_DEFAULTS["zie_memory_enabled"]

    def test_config_defaults_not_mutated_by_load_config(self, tmp_path):
        from utils import load_config, CONFIG_DEFAULTS
        original = dict(CONFIG_DEFAULTS)
        load_config(tmp_path)
        assert CONFIG_DEFAULTS == original
