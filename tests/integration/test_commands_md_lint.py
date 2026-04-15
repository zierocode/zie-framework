"""Integration tests: verify command .md files contain required output formatting strings."""
from pathlib import Path

import pytest

COMMANDS = Path(__file__).parents[2] / "commands"
ROOT = Path(__file__).parents[2]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def zie_implement_md():
    return (COMMANDS / "implement.md").read_text()


@pytest.fixture
def zie_audit_md():
    return (COMMANDS / "audit.md").read_text()


@pytest.fixture
def zie_resync_md():
    return (COMMANDS / "resync.md").read_text()


@pytest.fixture
def zie_sprint_md():
    return (COMMANDS / "sprint.md").read_text()


# ── T1: zie-implement ─────────────────────────────────────────────────────────

def test_zie_implement_task_counter_header(zie_implement_md):
    assert "[T{N}/{total}]" in zie_implement_md, (
        "zie-implement must print [T{N}/{total}] before each task"
    )


def test_zie_implement_phase_markers(zie_implement_md):
    for marker in ["→ RED", "→ GREEN", "→ REFACTOR"]:
        assert marker in zie_implement_md, (
            f"zie-implement must print phase marker: {marker}"
        )


def test_zie_implement_task_done_footer(zie_implement_md):
    assert "{remaining} remaining" in zie_implement_md, (
        "zie-implement must print '✓ T{N} done — {remaining} remaining' after each task"
    )


# ── T2: audit ─────────────────────────────────────────────────────────────

def test_zie_audit_phase_header(zie_audit_md):
    assert "[Phase" in zie_audit_md, (
        "audit must print [Phase N/M] headers"
    )


def test_zie_audit_agent_completion_marker(zie_audit_md):
    assert "Agent" in zie_audit_md and "✓" in zie_audit_md, (
        "audit must print Agent {X} (Domain) ✓ per spawned agent"
    )


def test_zie_audit_research_counter(zie_audit_md):
    assert "[Research" in zie_audit_md, (
        "audit must print [Research {N}/15] per search call"
    )


# ── T3: zie-resync ────────────────────────────────────────────────────────────

def test_zie_resync_bracketed_start(zie_resync_md):
    assert "[Exploring codebase...]" in zie_resync_md, (
        "zie-resync must print [Exploring codebase...] (bracketed)"
    )


def test_zie_resync_completion_summary(zie_resync_md):
    assert "knowledge_hash" in zie_resync_md and "synced_at" in zie_resync_md, (
        "zie-resync must print completion summary with knowledge_hash and synced_at"
    )


# ── T4: zie-sprint ────────────────────────────────────────────────────────────

def test_zie_sprint_task_create_per_phase(zie_sprint_md):
    assert zie_sprint_md.count("TaskCreate") >= 5, (
        "zie-sprint must call TaskCreate for each of 5 phases"
    )


def test_zie_sprint_task_update_per_phase(zie_sprint_md):
    assert zie_sprint_md.count("TaskUpdate") >= 5, (
        "zie-sprint must call TaskUpdate to mark each phase complete"
    )


def test_zie_sprint_progress_bar(zie_sprint_md):
    assert "████" in zie_sprint_md or "{done}/{total}" in zie_sprint_md, (
        "zie-sprint must print Unicode progress bar"
    )


def test_zie_sprint_eta_signal(zie_sprint_md):
    assert "phases remaining" in zie_sprint_md, (
        "zie-sprint must print phase-count ETA signal"
    )
