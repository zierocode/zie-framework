"""Tests for hooks/knowledge-hash.py"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
SCRIPT = REPO_ROOT / "hooks" / "knowledge-hash.py"


class TestKnowledgeHashScript:
    def test_script_exists(self):
        assert SCRIPT.exists(), f"knowledge-hash.py not found at {SCRIPT}"

    def test_output_is_64_char_hex(self, tmp_path):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True)
        assert result.returncode == 0
        output = result.stdout.strip()
        assert len(output) == 64
        assert all(c in "0123456789abcdef" for c in output)

    def test_same_input_produces_same_hash(self, tmp_path):
        (tmp_path / "subdir").mkdir()
        r1 = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True
        ).stdout.strip()
        r2 = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True
        ).stdout.strip()
        assert r1 == r2

    def test_default_root_runs_without_error(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=str(REPO_ROOT))
        assert result.returncode == 0
        assert len(result.stdout.strip()) == 64
