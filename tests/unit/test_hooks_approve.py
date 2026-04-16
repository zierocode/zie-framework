"""Tests for hooks/approve.py — sets approved:true in spec/plan frontmatter."""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
APPROVE = str(REPO_ROOT / "hooks" / "approve.py")


def run_approve(file_path: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, APPROVE, file_path],
        capture_output=True,
        text=True,
    )


class TestApproveScript:
    def test_flips_approved_false_to_true(self, tmp_path):
        f = tmp_path / "spec.md"
        f.write_text("---\napproved: false\napproved_at:\n---\n# Spec\n")
        r = run_approve(str(f))
        assert r.returncode == 0
        content = f.read_text()
        assert "approved: true" in content
        assert "approved: false" not in content

    def test_sets_approved_at_today(self, tmp_path):
        import datetime

        today = datetime.date.today().isoformat()
        f = tmp_path / "plan.md"
        f.write_text("---\napproved: false\napproved_at:\n---\n# Plan\n")
        run_approve(str(f))
        content = f.read_text()
        assert f"approved_at: {today}" in content

    def test_prints_approved_confirmation(self, tmp_path):
        f = tmp_path / "spec.md"
        f.write_text("---\napproved: false\napproved_at:\n---\n")
        r = run_approve(str(f))
        assert "Approved" in r.stdout or "approved" in r.stdout.lower()

    def test_exits_nonzero_on_missing_file(self):
        r = run_approve("/tmp/zie-nonexistent-spec-12345.md")
        assert r.returncode != 0

    def test_exits_nonzero_when_no_approved_false_field(self, tmp_path):
        f = tmp_path / "spec.md"
        f.write_text("# Spec without frontmatter\n")
        r = run_approve(str(f))
        assert r.returncode != 0

    def test_preserves_other_frontmatter_fields(self, tmp_path):
        f = tmp_path / "spec.md"
        f.write_text("---\napproved: false\napproved_at:\nbacklog: backlog/my-feature.md\n---\n# Spec\n")
        run_approve(str(f))
        content = f.read_text()
        assert "backlog: backlog/my-feature.md" in content

    def test_idempotent_on_already_approved(self, tmp_path):
        """Running approve.py on an already-approved file fails (nothing to flip)."""
        f = tmp_path / "spec.md"
        f.write_text("---\napproved: true\napproved_at: 2026-04-10\n---\n")
        r = run_approve(str(f))
        # Should exit non-zero — no approved:false to flip
        assert r.returncode != 0

    def test_exits_nonzero_with_no_args(self):
        r = subprocess.run([sys.executable, APPROVE], capture_output=True, text=True)
        assert r.returncode != 0
