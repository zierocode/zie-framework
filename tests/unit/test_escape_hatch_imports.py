"""Smoke test — all new modules and symbols importable."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))


def test_utils_drift_importable():
    import utils_drift  # noqa: F401
    assert hasattr(utils_drift, "append_drift_event")
    assert hasattr(utils_drift, "read_drift_count")
    assert hasattr(utils_drift, "close_drift_track")


def test_is_track_active_importable():
    from utils_roadmap import is_track_active
    assert callable(is_track_active)
