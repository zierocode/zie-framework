#!/usr/bin/env python3
"""Self-tuning proposal helpers for /zie-retro."""
import re

# Pattern: commit mentions "RED" + numeric day count
_RED_DURATION_RE = re.compile(
    r'\bRED\b.*?(\d+)\s*day',
    re.IGNORECASE,
)


def parse_red_cycle_durations_from_log(log: str) -> list:
    """Parse approximate RED cycle durations (in days) from git log oneline output.

    Returns a list of int durations, capped at 5 cycles (most recent first).
    Only includes commits where a numeric day count is found alongside RED.
    """
    durations = []
    for line in log.splitlines():
        if not re.search(r'\bRED\b', line, re.IGNORECASE):
            continue
        m = _RED_DURATION_RE.search(line)
        if m:
            try:
                durations.append(int(m.group(1)))
            except ValueError:
                pass
        if len(durations) >= 5:
            break
    return durations


def build_tuning_proposals(config: dict, red_durations: list, recent_log: str) -> list:
    """Build list of config change proposals based on observed patterns.

    Returns list of dicts: [{key, from_val, to_val, reason}].
    At most 3 proposals returned.
    """
    proposals = []

    # Proposal 1: auto_test_max_wait_s — if avg RED cycle > 3 days
    if red_durations:
        avg_days = sum(red_durations) / len(red_durations)
        if avg_days > 3:
            current = config.get("auto_test_max_wait_s", 15)
            proposals.append({
                "key": "auto_test_max_wait_s",
                "from_val": current,
                "to_val": 30,
                "reason": f"RED cycles averaged {avg_days:.1f} days across last {len(red_durations)} cycles",
            })

    # Proposal 2: safety_check_mode — if "agent" and no BLOCKs in recent log
    if config.get("safety_check_mode") == "agent":
        if "BLOCK" not in recent_log:
            proposals.append({
                "key": "safety_check_mode",
                "from_val": "agent",
                "to_val": "regex",
                "reason": "no agent-level blocks in last 10 sessions",
            })

    return proposals[:3]
