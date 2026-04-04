"""Tests for self-tuning proposal logic extracted from /zie-retro."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
from utils_self_tuning import (
    build_tuning_proposals,
    parse_red_cycle_durations_from_log,
)


class TestParseRedCycleDurations:
    def test_returns_empty_on_no_red_commits(self):
        log = "abc1234 feat: add new feature\ndef5678 fix: resolve bug\n"
        result = parse_red_cycle_durations_from_log(log)
        assert result == []

    def test_detects_red_stuck_commit(self):
        log = "abc1234 RED phase stuck for 3 days — split task\n"
        result = parse_red_cycle_durations_from_log(log)
        assert 3 in result

    def test_detects_red_slow_commit(self):
        log = "abc1234 RED: slow going, took 5 days\n"
        result = parse_red_cycle_durations_from_log(log)
        assert 5 in result

    def test_returns_at_most_5_cycles(self):
        log = "\n".join(
            [f"abc{i} RED phase stuck {i+2} days" for i in range(10)]
        )
        result = parse_red_cycle_durations_from_log(log)
        assert len(result) <= 5

    def test_ignores_commits_without_duration_word(self):
        log = "abc1234 RED phase completed\n"
        result = parse_red_cycle_durations_from_log(log)
        assert result == []


class TestBuildTuningProposals:
    def test_no_proposals_when_no_patterns(self):
        config = {"auto_test_max_wait_s": 15, "safety_check_mode": "regex"}
        proposals = build_tuning_proposals(config, red_durations=[], recent_log="")
        assert proposals == []

    def test_proposes_auto_test_wait_when_avg_exceeds_3_days(self):
        config = {"auto_test_max_wait_s": 15, "safety_check_mode": "regex"}
        proposals = build_tuning_proposals(config, red_durations=[4, 5, 3, 4, 5], recent_log="")
        keys = [p["key"] for p in proposals]
        assert "auto_test_max_wait_s" in keys

    def test_no_auto_test_proposal_when_avg_under_3_days(self):
        config = {"auto_test_max_wait_s": 15, "safety_check_mode": "regex"}
        proposals = build_tuning_proposals(config, red_durations=[1, 2, 1], recent_log="")
        keys = [p["key"] for p in proposals]
        assert "auto_test_max_wait_s" not in keys

    def test_proposes_safety_mode_when_agent_and_no_blocks(self):
        config = {"auto_test_max_wait_s": 15, "safety_check_mode": "agent"}
        recent_log = "abc feat: add thing\ndef fix: small bug\n"
        proposals = build_tuning_proposals(config, red_durations=[], recent_log=recent_log)
        keys = [p["key"] for p in proposals]
        assert "safety_check_mode" in keys

    def test_no_safety_mode_proposal_when_blocks_present(self):
        config = {"auto_test_max_wait_s": 15, "safety_check_mode": "agent"}
        recent_log = "abc BLOCK: safety check blocked rm -rf\n"
        proposals = build_tuning_proposals(config, red_durations=[], recent_log=recent_log)
        keys = [p["key"] for p in proposals]
        assert "safety_check_mode" not in keys

    def test_at_most_3_proposals(self):
        config = {"auto_test_max_wait_s": 15, "safety_check_mode": "agent"}
        proposals = build_tuning_proposals(config, red_durations=[4, 5, 4, 5, 4], recent_log="no blocks")
        assert len(proposals) <= 3
