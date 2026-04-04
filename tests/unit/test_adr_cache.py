"""Tests for get_cached_adrs and write_adr_cache in hooks/utils.py."""
import json
import os
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from utils_roadmap import get_cached_adrs, write_adr_cache


class TestGetCachedAdrs:
    def test_miss_when_no_cache_file(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        result = get_cached_adrs("sess-adr-001", decisions)
        assert result is None

    def test_hit_when_mtime_matches(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        adr = decisions / "ADR-001.md"
        adr.write_text("# ADR-001")
        content = "# ADR-001"
        ok, _ = write_adr_cache("sess-adr-002", content, decisions, tmp_dir=tmp_path)
        assert ok is True
        result = get_cached_adrs("sess-adr-002", decisions, tmp_dir=tmp_path)
        assert result == content

    def test_miss_when_adr_newer_than_cache(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        adr = decisions / "ADR-001.md"
        adr.write_text("# ADR-001")
        write_adr_cache("sess-adr-003", "# ADR-001", decisions, tmp_dir=tmp_path)
        future = time.time() + 10
        os.utime(adr, (future, future))
        result = get_cached_adrs("sess-adr-003", decisions, tmp_dir=tmp_path)
        assert result is None

    def test_miss_when_decisions_dir_missing(self, tmp_path):
        result = get_cached_adrs("sess-adr-004", tmp_path / "nonexistent", tmp_dir=tmp_path)
        assert result is None

    def test_miss_when_decisions_dir_empty(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        result = get_cached_adrs("sess-adr-005", decisions, tmp_dir=tmp_path)
        assert result is None

    def test_session_id_sanitized(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        write_adr_cache("../evil/id", "content", decisions, tmp_dir=tmp_path)
        for root, dirs, files in os.walk(str(tmp_path)):
            for f in files:
                full = os.path.join(root, f)
                assert full.startswith(str(tmp_path)), f"file escaped tmp: {full}"

    def test_returns_none_on_read_error(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        write_adr_cache("sess-adr-006", "# ADR-001", decisions, tmp_dir=tmp_path)
        cache_path = tmp_path / "zie-sess-adr-006" / "adr-cache.json"
        cache_path.write_text("not valid json")
        result = get_cached_adrs("sess-adr-006", decisions, tmp_dir=tmp_path)
        assert result is None


class TestWriteAdrCache:
    def test_returns_true_on_success(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        result = write_adr_cache("sess-adr-w01", "# ADR-001", decisions, tmp_dir=tmp_path)
        assert result[0] is True
        assert result[1] is not None
        assert result[1].exists()

    def test_success_path_matches_expected_location(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        result = write_adr_cache("sess-adr-w01b", "# ADR-001", decisions, tmp_dir=tmp_path)
        expected = tmp_path / "zie-sess-adr-w01b" / "adr-cache.json"
        assert result == (True, expected)

    def test_returns_false_when_decisions_empty(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        result = write_adr_cache("sess-adr-w02", "", decisions, tmp_dir=tmp_path)
        assert result == (False, None)

    def test_returns_false_when_decisions_missing(self, tmp_path):
        result = write_adr_cache("sess-adr-w03", "", tmp_path / "nonexistent", tmp_dir=tmp_path)
        assert result == (False, None)

    def test_cache_file_has_correct_structure(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        adr = decisions / "ADR-001.md"
        adr.write_text("# ADR-001")
        write_adr_cache("sess-adr-w04", "# ADR-001", decisions, tmp_dir=tmp_path)
        cache_path = tmp_path / "zie-sess-adr-w04" / "adr-cache.json"
        assert cache_path.exists()
        data = json.loads(cache_path.read_text())
        assert "mtime" in data
        assert data["content"] == "# ADR-001"
        assert data["mtime"] == pytest.approx(adr.stat().st_mtime, abs=0.01)

    def test_returns_false_on_symlink(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        cache_dir = tmp_path / "zie-sess-adr-w05"
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / "adr-cache.json"
        link_target = tmp_path / "other.json"
        link_target.write_text("{}")
        cache_file.symlink_to(link_target)
        result = write_adr_cache("sess-adr-w05", "# ADR-001", decisions, tmp_dir=tmp_path)
        assert result == (False, None)

    def test_silently_returns_false_on_os_error(self, tmp_path, monkeypatch):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        monkeypatch.setattr(Path, "mkdir", lambda *a, **kw: (_ for _ in ()).throw(OSError("no perms")))
        result = write_adr_cache("sess-adr-w06", "# ADR-001", decisions, tmp_dir=tmp_path)
        assert result == (False, None)
