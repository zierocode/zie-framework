"""Tests for make adr-count Makefile target."""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def test_adr_count_exits_zero():
    result = subprocess.run(
        ["make", "adr-count"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"make adr-count exited {result.returncode}: {result.stderr}"


def test_adr_count_prints_integer():
    result = subprocess.run(
        ["make", "adr-count"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip().splitlines()
    numeric_lines = [line for line in output if line.strip().isdigit()]
    assert numeric_lines, f"No integer line in output: {result.stdout!r}"
