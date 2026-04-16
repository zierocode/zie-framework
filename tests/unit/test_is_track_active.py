"""Tests for utils_roadmap.is_track_active."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_roadmap import is_track_active


def _make_cwd(tmp_path, roadmap_content=None, drift_lines=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap_content is not None:
        (zf / "ROADMAP.md").write_text(roadmap_content)
    if drift_lines is not None:
        (zf / ".drift-log").write_text("\n".join(drift_lines) + "\n")
    return tmp_path


class TestIsTrackActive:
    def test_now_lane_open_item_returns_true(self, tmp_path):
        cwd = _make_cwd(tmp_path, "## Now\n- [ ] my-feature\n## Next\n")
        assert is_track_active(cwd) is True

    def test_now_lane_only_closed_items_returns_false(self, tmp_path):
        cwd = _make_cwd(tmp_path, "## Now\n- [x] my-feature\n## Next\n")
        assert is_track_active(cwd) is False

    def test_now_lane_empty_returns_false(self, tmp_path):
        cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n")
        assert is_track_active(cwd) is False

    def test_missing_roadmap_returns_false(self, tmp_path):
        cwd = _make_cwd(tmp_path)  # no ROADMAP.md
        assert is_track_active(cwd) is False

    def test_open_drift_marker_returns_true(self, tmp_path):
        event = json.dumps({"track": "hotfix", "slug": "abc", "closed_at": None})
        cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n", [event])
        assert is_track_active(cwd) is True

    def test_closed_drift_marker_returns_false(self, tmp_path):
        event = json.dumps({"track": "hotfix", "slug": "abc", "closed_at": "2026-04-04T00:00:00"})
        cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n", [event])
        assert is_track_active(cwd) is False

    def test_unreadable_drift_log_does_not_raise(self, tmp_path):
        cwd = _make_cwd(tmp_path, "## Now\n\n## Next\n", ["not-json"])
        assert is_track_active(cwd) is False
