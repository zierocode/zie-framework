"""Tests for knowledge-hash.py --check mode."""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(REPO_ROOT, "hooks", "knowledge-hash.py")


def run_check(root_dir):
    return subprocess.run(
        [sys.executable, SCRIPT, "--check", "--root", str(root_dir)],
        capture_output=True, text=True,
    )


def write_config(root_dir, knowledge_hash=""):
    zf = Path(root_dir) / "zie-framework"
    zf.mkdir(parents=True, exist_ok=True)
    (zf / ".config").write_text(json.dumps({"knowledge_hash": knowledge_hash}))


class TestCheckModeHashMismatch:
    def test_prints_drift_warning_on_mismatch(self, tmp_path):
        """Stored hash differs from computed → drift warning printed."""
        write_config(tmp_path, knowledge_hash="deadbeef0000")
        r = run_check(tmp_path)
        assert r.returncode == 0
        assert "[zie-framework] Knowledge drift detected" in r.stdout
        assert "/zie-resync" in r.stdout

    def test_drift_message_exact_text(self, tmp_path):
        write_config(tmp_path, knowledge_hash="aaaaaaaaaaaa")
        r = run_check(tmp_path)
        assert (
            "[zie-framework] Knowledge drift detected since last session"
            " — run /zie-resync to update project context"
        ) in r.stdout


class TestCheckModeSilentCases:
    def test_silent_when_hashes_match(self, tmp_path):
        """When stored hash equals computed hash → no output."""
        compute = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        current_hash = compute.stdout.strip()
        write_config(tmp_path, knowledge_hash=current_hash)
        r = run_check(tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_silent_when_stored_hash_empty(self, tmp_path):
        """Empty knowledge_hash → skip check silently."""
        write_config(tmp_path, knowledge_hash="")
        r = run_check(tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_silent_when_key_absent(self, tmp_path):
        """Missing knowledge_hash key → skip check silently."""
        zf = tmp_path / "zie-framework"
        zf.mkdir(parents=True)
        (zf / ".config").write_text(json.dumps({"project_type": "python-api"}))
        r = run_check(tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_silent_when_config_missing(self, tmp_path):
        """No .config file → skip check silently."""
        r = run_check(tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_silent_when_config_corrupt(self, tmp_path):
        """Corrupt .config → skip check silently, never crash."""
        zf = tmp_path / "zie-framework"
        zf.mkdir(parents=True)
        (zf / ".config").write_text("not valid json!!!")
        r = run_check(tmp_path)
        assert r.returncode == 0


class TestDefaultModeUnchanged:
    def test_default_still_prints_hash(self, tmp_path):
        """Default mode (no --check) still prints hex hash to stdout."""
        r = subprocess.run(
            [sys.executable, SCRIPT, "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert len(r.stdout.strip()) == 64  # SHA-256 hex
