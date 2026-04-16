"""Tests for status pipeline detail: problem excerpts and spec/plan status."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_roadmap import check_spec_plan_status, extract_problem_excerpt


class TestExtractProblemExcerpt:
    def test_extracts_problem_text(self, tmp_path):
        backlog = tmp_path / "backlog"
        backlog.mkdir()
        (backlog / "my-feature.md").write_text(
            "# My Feature\n\n## Problem\n\nUsers cannot export data.\n\n## Rough Scope\n\nExport button."
        )
        result = extract_problem_excerpt("my-feature", backlog)
        assert "Users cannot export data" in result

    def test_truncates_long_text(self, tmp_path):
        backlog = tmp_path / "backlog"
        backlog.mkdir()
        long_text = "A" * 200
        (backlog / "long-item.md").write_text(f"# Long\n\n## Problem\n\n{long_text}\n\n## Scope")
        result = extract_problem_excerpt("long-item", backlog, max_len=120)
        assert len(result) <= 124  # 120 + "…"
        assert result.endswith("…")

    def test_missing_file_returns_no_description(self, tmp_path):
        result = extract_problem_excerpt("nonexistent", tmp_path)
        assert result == "(no description)"

    def test_no_problem_section_returns_no_description(self, tmp_path):
        backlog = tmp_path / "backlog"
        backlog.mkdir()
        (backlog / "no-problem.md").write_text("# No Problem\n\nJust a title")
        result = extract_problem_excerpt("no-problem", backlog)
        assert result == "(no description)"

    def test_multiline_problem_collapsed(self, tmp_path):
        backlog = tmp_path / "backlog"
        backlog.mkdir()
        (backlog / "multi.md").write_text("# Multi\n\n## Problem\n\nLine one.\nLine two.\nLine three.\n\n## Scope")
        result = extract_problem_excerpt("multi", backlog)
        assert "\n" not in result
        assert "Line one. Line two. Line three." in result


class TestCheckSpecPlanStatus:
    def test_both_exist(self, tmp_path):
        specs = tmp_path / "specs"
        plans = tmp_path / "plans"
        specs.mkdir()
        plans.mkdir()
        (specs / "2026-04-15-my-feature-design.md").write_text("---\n---")
        (plans / "2026-04-15-my-feature.md").write_text("---\n---")
        spec, plan = check_spec_plan_status("my-feature", specs, plans)
        assert spec is True
        assert plan is True

    def test_neither_exists(self, tmp_path):
        specs = tmp_path / "specs"
        plans = tmp_path / "plans"
        specs.mkdir()
        plans.mkdir()
        spec, plan = check_spec_plan_status("nonexistent", specs, plans)
        assert spec is False
        assert plan is False

    def test_spec_only(self, tmp_path):
        specs = tmp_path / "specs"
        plans = tmp_path / "plans"
        specs.mkdir()
        plans.mkdir()
        (specs / "2026-04-15-my-feature-design.md").write_text("---\n---")
        spec, plan = check_spec_plan_status("my-feature", specs, plans)
        assert spec is True
        assert plan is False
