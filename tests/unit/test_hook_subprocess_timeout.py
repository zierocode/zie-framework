"""
Error-path tests: hooks must exit 0 when subprocess calls time out.
Uses importlib.util to load hook in-process and mock.patch to inject TimeoutExpired.
"""

import importlib.util
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


def _load_hook(name: str):
    """Return (spec, mod) for a hook — does NOT exec the module yet."""
    hook_path = REPO_ROOT / "hooks" / name
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").replace(".", "_"), hook_path)
    mod = importlib.util.module_from_spec(spec)
    return spec, mod


@pytest.mark.error_path
def test_safety_check_agent_timeout_falls_back(tmp_path):
    """safety_check_agent.py must not raise when its Claude subprocess times out."""
    spec, mod = _load_hook("safety_check_agent.py")
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=5)
        try:
            spec.loader.exec_module(mod)
        except SystemExit as e:
            assert e.code == 0 or e.code is None
        except Exception:
            pytest.fail("safety_check_agent raised unexpectedly on TimeoutExpired")


@pytest.mark.error_path
def test_auto_test_make_hang_exits_cleanly(tmp_path):
    """auto-test.py must not raise when make subprocess times out."""
    spec, mod = _load_hook("auto-test.py")
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="make", timeout=60)
        try:
            spec.loader.exec_module(mod)
        except SystemExit as e:
            assert e.code == 0 or e.code is None
        except Exception:
            pytest.fail("auto-test raised unexpectedly on TimeoutExpired")
