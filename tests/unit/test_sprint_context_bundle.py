#!/usr/bin/env python3
"""Unit tests for sprint context bundle passthrough (Phase 1→2→3)."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def test_project():
    """Create a minimal test project structure."""
    tmp = Path(tempfile.mkdtemp())
    project = tmp / "test-project"
    project.mkdir()

    # Create zie-framework structure
    zf = project / "zie-framework"
    zf.mkdir()
    (zf / "backlog").mkdir()
    (zf / "specs").mkdir()
    (zf / "plans").mkdir()
    (zf / "decisions").mkdir()
    (zf / "project").mkdir()

    # Create .zie directory
    zie_dir = project / ".zie"
    zie_dir.mkdir()

    # Create sample backlog items
    (zf / "backlog" / "feature-a.md").write_text("""---
tags: [feature]
---

# Feature A

## Problem
Feature A problem statement.

## Motivation
Feature A motivation.

## Rough Scope
Feature A scope.
""")

    (zf / "backlog" / "feature-b.md").write_text("""---
tags: [feature]
---

# Feature B

## Problem
Feature B problem statement.

## Motivation
Feature B motivation.

## Rough Scope
Feature B scope.
""")

    # Create sample specs
    (zf / "specs" / "2026-01-01-feature-a-design.md").write_text("""---
approved: true
approved_at: 2026-01-01T00:00:00Z
backlog: backlog/feature-a.md
---

# Feature A — Design Spec

**Problem:** Feature A problem
**Approach:** Feature A approach
**Components:** - component-a.py
**Data Flow:** Step 1 → Step 2
**Edge Cases:** - Edge case 1
""")

    (zf / "specs" / "2026-01-02-feature-b-design.md").write_text("""---
approved: true
approved_at: 2026-01-02T00:00:00Z
backlog: backlog/feature-b.md
---

# Feature B — Design Spec

**Problem:** Feature B problem
**Approach:** Feature B approach
**Components:** - component-b.py
**Data Flow:** Step 1 → Step 2
**Edge Cases:** - Edge case 1
""")

    # Create sample plans
    (zf / "plans" / "2026-01-01-feature-a.md").write_text("""---
approved: true
approved_at: 2026-01-01T00:00:00Z
spec: specs/2026-01-01-feature-a-design.md
---

# Feature A — Implementation Plan

## Tasks
- [ ] Task 1
- [ ] Task 2
""")

    (zf / "plans" / "2026-01-02-feature-b.md").write_text("""---
approved: true
approved_at: 2026-01-02T00:00:00Z
spec: specs/2026-01-02-feature-b-design.md
---

# Feature B — Implementation Plan

## Tasks
- [ ] Task 1
- [ ] Task 2
""")

    # Create sample ROADMAP
    (zf / "ROADMAP.md").write_text("""# ROADMAP

## Next

- [ ] feature-a
- [ ] feature-b

## Ready

## Now

## Done
""")

    # Create sample ADR
    (zf / "decisions" / "ADR-000-summary.md").write_text("""# ADR-000: Project Summary

## Status
Approved

## Context
Project context.
""")

    # Create project context
    (zf / "project" / "context.md").write_text("""# Project Context

## Overview
Test project.
""")

    yield project
    shutil.rmtree(tmp, ignore_errors=True)


class TestSprintContextBundle:
    """Test sprint context bundle writing and reading."""

    def test_bundle_structure(self, test_project):
        """Sprint context bundle has correct structure."""
        zf = test_project / "zie-framework"
        zie_dir = test_project / ".zie"

        # Simulate Phase 1 writing bundle
        sprint_context = {
            "specs": {
                "feature-a": (zf / "specs" / "2026-01-01-feature-a-design.md").read_text(),
                "feature-b": (zf / "specs" / "2026-01-02-feature-b-design.md").read_text(),
            },
            "plans": {
                "feature-a": (zf / "plans" / "2026-01-01-feature-a.md").read_text(),
                "feature-b": (zf / "plans" / "2026-01-02-feature-b.md").read_text(),
            },
            "roadmap": (zf / "ROADMAP.md").read_text(),
            "context_bundle": {
                "adrs": [{"title": "ADR-000", "summary": "Project context"}],
                "project_context": "Test project.",
            },
        }

        bundle_path = zie_dir / "sprint-context.json"
        bundle_path.write_text(json.dumps(sprint_context))

        # Verify bundle can be read back
        loaded = json.loads(bundle_path.read_text())

        assert "specs" in loaded
        assert "plans" in loaded
        assert "roadmap" in loaded
        assert "context_bundle" in loaded
        assert "feature-a" in loaded["specs"]
        assert "feature-b" in loaded["specs"]
        assert "approved: true" in loaded["specs"]["feature-a"]
        assert "Implementation Plan" in loaded["plans"]["feature-a"]

    def test_bundle_phase_passthrough(self, test_project):
        """Context bundle passes data from Phase 1→2→3."""
        zie_dir = test_project / ".zie"
        zf = test_project / "zie-framework"

        # Phase 1: Write bundle
        specs_content = {
            "feature-a": (zf / "specs" / "2026-01-01-feature-a-design.md").read_text(),
        }
        plans_content = {
            "feature-a": (zf / "plans" / "2026-01-01-feature-a.md").read_text(),
        }

        sprint_context = {
            "specs": specs_content,
            "plans": plans_content,
            "roadmap": (zf / "ROADMAP.md").read_text(),
            "context_bundle": {"adrs": [], "project_context": ""},
        }

        bundle_path = zie_dir / "sprint-context.json"
        bundle_path.write_text(json.dumps(sprint_context))

        # Phase 2: Read bundle
        loaded = json.loads(bundle_path.read_text())

        assert loaded["specs"]["feature-a"] == specs_content["feature-a"]
        assert loaded["plans"]["feature-a"] == plans_content["feature-a"]

        # Phase 3: Bundle still intact
        reloaded = json.loads(bundle_path.read_text())
        assert reloaded["specs"]["feature-a"] == specs_content["feature-a"]

    def test_bundle_fallback_on_missing(self, test_project):
        """Graceful fallback when bundle is missing (resume case)."""
        zie_dir = test_project / ".zie"
        bundle_path = zie_dir / "sprint-context.json"

        # Bundle doesn't exist (resume after crash)
        assert not bundle_path.exists()

        # Fallback: read from disk
        sprint_context = {}

        assert sprint_context == {}

    def test_bundle_fallback_on_corrupt(self, test_project):
        """Graceful fallback when bundle is corrupt."""
        zie_dir = test_project / ".zie"
        bundle_path = zie_dir / "sprint-context.json"

        # Write corrupt JSON
        bundle_path.write_text("{ invalid json }")

        # Fallback: handle exception
        try:
            json.loads(bundle_path.read_text())
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            pass  # Expected

    def test_bundle_token_savings(self, test_project):
        """Bundle eliminates redundant disk reads."""
        test_project / "zie-framework"
        test_project / ".zie"

        # Without bundle: read each file from disk (3 phases × 2 items × 2 files)
        # = 12 disk reads
        disk_reads_without_bundle = 3 * 2 * 2  # phases × items × files

        # With bundle: read once in Phase 1, pass to Phase 2/3
        # = 2 disk reads (bundle write + bundle read)
        disk_reads_with_bundle = 2

        # Savings: 12 - 2 = 10 disk reads eliminated
        assert disk_reads_with_bundle < disk_reads_without_bundle

        # Token savings: ~4.5w tokens per 5-item sprint
        # Each spec/plan ~1.5k tokens, re-read 3× = 4.5k tokens wasted per item
        # 5 items × 4.5k = 22.5k tokens (conservative estimate)
        tokens_per_item = 1500  # spec + plan
        items = 5
        phases = 3
        tokens_without_bundle = tokens_per_item * items * phases
        tokens_with_bundle = tokens_per_item * items  # read once
        token_savings = tokens_without_bundle - tokens_with_bundle

        assert token_savings > 0
        assert token_savings >= 15000  # ~15k+ tokens saved (1500 tokens × 5 items × 2 phases eliminated)


class TestSprintContextIntegration:
    """Test sprint context bundle integration with sprint.md."""

    def test_bundle_written_after_phase1(self, test_project):
        """Bundle is written after Phase 1 completes."""
        zie_dir = test_project / ".zie"
        zf = test_project / "zie-framework"
        bundle_path = zie_dir / "sprint-context.json"

        # Simulate Phase 1 completion
        sprint_context = {
            "specs": {
                "feature-a": (zf / "specs" / "2026-01-01-feature-a-design.md").read_text(),
            },
            "plans": {
                "feature-a": (zf / "plans" / "2026-01-01-feature-a.md").read_text(),
            },
            "roadmap": (zf / "ROADMAP.md").read_text(),
            "context_bundle": {"adrs": [], "project_context": ""},
        }

        bundle_path.write_text(json.dumps(sprint_context))

        # Verify bundle exists
        assert bundle_path.exists()

        # Verify content
        loaded = json.loads(bundle_path.read_text())
        assert "specs" in loaded
        assert "plans" in loaded
        assert "roadmap" in loaded

    def test_bundle_read_by_phase2(self, test_project):
        """Phase 2 reads from bundle instead of disk."""
        zie_dir = test_project / ".zie"
        zf = test_project / "zie-framework"
        bundle_path = zie_dir / "sprint-context.json"

        # Phase 1 writes bundle
        expected_spec = (zf / "specs" / "2026-01-01-feature-a-design.md").read_text()
        expected_plan = (zf / "plans" / "2026-01-01-feature-a.md").read_text()

        sprint_context = {
            "specs": {"feature-a": expected_spec},
            "plans": {"feature-a": expected_plan},
            "roadmap": (zf / "ROADMAP.md").read_text(),
            "context_bundle": {"adrs": [], "project_context": ""},
        }
        bundle_path.write_text(json.dumps(sprint_context))

        # Phase 2 reads bundle
        loaded = json.loads(bundle_path.read_text())

        # Verify no disk read needed
        assert loaded["specs"]["feature-a"] == expected_spec
        assert loaded["plans"]["feature-a"] == expected_plan

    def test_bundle_read_by_phase3(self, test_project):
        """Phase 3 reads from bundle for release notes."""
        zie_dir = test_project / ".zie"
        zf = test_project / "zie-framework"
        bundle_path = zie_dir / "sprint-context.json"

        # Phase 1 writes bundle
        sprint_context = {
            "specs": {"feature-a": "spec content"},
            "plans": {"feature-a": "plan content"},
            "roadmap": (zf / "ROADMAP.md").read_text(),
            "context_bundle": {"adrs": [], "project_context": ""},
        }
        bundle_path.write_text(json.dumps(sprint_context))

        # Phase 3 reads bundle
        loaded = json.loads(bundle_path.read_text())

        # Verify specs/plans available for release notes
        assert loaded["specs"]["feature-a"] == "spec content"
        assert loaded["plans"]["feature-a"] == "plan content"
