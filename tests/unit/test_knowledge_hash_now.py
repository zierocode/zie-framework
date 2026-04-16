import subprocess
import sys
from pathlib import Path

REPO_ROOT = str(Path(__file__).parent.parent.parent)


def test_now_flag_exits_zero():
    result = subprocess.run(
        [sys.executable, "hooks/knowledge-hash.py", "--now"], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}: {result.stderr}"


def test_now_flag_prints_hash():
    result = subprocess.run(
        [sys.executable, "hooks/knowledge-hash.py", "--now"], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert len(result.stdout.strip()) == 64, f"Expected 64-char hash, got: {result.stdout.strip()!r}"


def test_now_with_root_flag(tmp_path):
    result = subprocess.run(
        [sys.executable, "hooks/knowledge-hash.py", "--now", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert len(result.stdout.strip()) == 64


def test_existing_behavior_unchanged():
    """Without --now, should still print hash and exit 0."""
    result = subprocess.run([sys.executable, "hooks/knowledge-hash.py"], capture_output=True, text=True, cwd=REPO_ROOT)
    assert result.returncode == 0
    assert len(result.stdout.strip()) == 64
