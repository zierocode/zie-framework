"""
Error-path tests: concurrent hook execution must not corrupt state or crash.
Simulates session-cleanup deleting /tmp/zie-<session> while notification-log writes.
"""

import os
import shutil
import threading
from pathlib import Path

import pytest


def _run_cleanup(session_dir: Path, results: list, idx: int):
    """Delete the session tmp dir to simulate session-cleanup.py behavior."""
    try:
        shutil.rmtree(session_dir, ignore_errors=True)
        results[idx] = "ok"
    except Exception as e:
        results[idx] = f"error: {e}"


def _run_notification_write(session_dir: Path, results: list, idx: int):
    """Attempt to write to notification.log inside the session dir."""
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        log_path = session_dir / "notification.log"
        try:
            with open(log_path, "a") as f:
                f.write("test notification\n")
        except OSError:
            pass  # ENOENT/OSError: hook exits 0 — not a crash
        results[idx] = "ok"
    except Exception as e:
        results[idx] = f"error: {e}"


@pytest.mark.error_path
def test_concurrent_cleanup_and_notification_log(tmp_path, run_hook):
    """
    session-cleanup deletes /tmp/zie-<session> while notification-log.py writes.
    Both operations must complete without raising — simulates the ENOENT race.
    """
    session_id = f"test-concurrent-{os.getpid()}"
    session_dir = Path(f"/tmp/zie-{session_id}")
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "notification.log").write_text("")

    results = [None, None]

    t_cleanup = threading.Thread(target=_run_cleanup, args=(session_dir, results, 0))
    t_write = threading.Thread(target=_run_notification_write, args=(session_dir, results, 1))

    t_cleanup.start()
    t_write.start()
    t_cleanup.join(timeout=5)
    t_write.join(timeout=5)

    assert results[0] == "ok", f"cleanup thread failed: {results[0]}"
    assert results[1] == "ok", f"notification write thread failed: {results[1]}"

    # Verify the actual notification-log.py hook exits 0 with missing session dir
    shutil.rmtree(session_dir, ignore_errors=True)
    cwd = tmp_path / "proj"
    cwd.mkdir()
    (cwd / "zie-framework").mkdir()

    r_notif = run_hook(
        "notification-log.py",
        {"notification_type": "permission_prompt", "message": "test"},
        tmp_cwd=cwd,
        extra_env={"CLAUDE_SESSION_ID": session_id},
    )
    assert r_notif.returncode == 0
