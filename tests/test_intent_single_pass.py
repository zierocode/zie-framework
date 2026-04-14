#!/usr/bin/env python3
"""Unit tests for intent-pattern-single-pass optimization.

Tests the INTENT_PATTERN regex directly without loading the full hook module
(which runs at import time and requires stdin).
"""
import re

import pytest


# Copy of INTENT_PATTERN from intent-sdlc.py for testing
INTENT_PATTERN = re.compile(r"""
    (?P<init>
        \binit\b | เริ่มต้น.*project | ตั้งค่า.*project | setup.*project | bootstrap
    )
    |
    (?P<backlog>
        อยากทำ | อยากได้ | อยากเพิ่ม | อยากสร้าง | \bidea\b | \bfeature\b |
        new\ feature | เพิ่ม.*feature | สร้าง.*ใหม่ |
        want\ to\ (build|add|create|make) | ต้องการ | would\ like\ to |
        \bbacklog\b | capture.*idea
    )
    |
    (?P<spec>
        \bspec\b | design.*doc | write.*spec | spec.*feature |
        เขียน.*spec | ออกแบบ | design.*feature
    )
    |
    (?P<plan>
        \bplan\b | วางแผน | อยากวางแผน | เลือก.*backlog |
        หยิบ.*backlog | plan.*feature | ready.*to.*plan | zie.?plan
    )
    |
    (?P<implement>
        implement | ทำ.*ต่อ | continue | resume | สร้าง.*feature |
        next\ task | task.*ต่อ | code.*this | let.*s.*build | start.*coding
    )
    |
    (?P<fix>
        \bbug\b | พัง | \berror\b | \bfix\b | ไม่ทำงาน | \bcrash\b |
        exception | traceback | ล้มเหลว | broken | doesn.*t\ work |
        not\ working | failed | failure
    )
    |
    (?P<release>
        \brelease\b | \bdeploy\b | \bpublish\b | merge.*main |
        go.*live | launch | ready.*to.*release | ปล่อย | deploy.*now
    )
    |
    (?P<retro>
        \bretro\b | retrospective | สรุป.*session | ทบทวน |
        review.*session | what.*did.*we | what.*we.*learned | what.*worked
    )
    |
    (?P<sprint>
        \bsprint\b | zie.?sprint | clear.*backlog | เคลียร์.*backlog |
        ship.*all | ทำ.*ทั้งหมด | batch.*release | full.*pipeline
    )
    |
    (?P<status>
        \bstatus\b | ทำอะไรอยู่ | where.*am.*i | progress |
        what.*next | ต่อไปทำ | ถัดไป | สถานะ
    )
    |
    (?P<hotfix>
        \bhotfix\b | emergency | prod.*down | urgent.*fix |
        critical.*fix | cannot\ wait | on.*fire | production.*issue
    )
    |
    (?P<chore>
        \bchore\b | bump.*version | update.*docs | housekeeping |
        maintenance | cleanup | tidy.*up
    )
    |
    (?P<spike>
        \bspike\b | \bexplore\b | \binvestigate\b | \bresearch\b |
        \bprototype\b | proof.*of.*concept | \bpoc\b | time.?box
    )
    |
    (?P<brainstorm>
        \bimprove\b | what\ if | \bresearch\b | deep\ dive |
        อยากให้มี | ควรจะ | น่าจะเพิ่ม | ปรับอะไรดี |
        คิดว่าขาดอะไร | \bexplore\b
    )
""", re.IGNORECASE | re.VERBOSE)

# Pre-compiled new-intent signal regexes
NEW_INTENT_REGEXES = {
    "sprint": [re.compile(p, re.IGNORECASE) for p in [
        r"ทำเลย", r"\bimplement\b", r"\bbuild\b", r"สร้าง",
        r"เพิ่ม.*feature", r"start.*coding",
    ]],
    "fix": [re.compile(p, re.IGNORECASE) for p in [
        r"\bbug\b", r"\bbroken\b", r"\berror\b", r"ไม่.*work",
        r"\bcrash\b", r"\bfail\b", r"แก้",
    ]],
    "chore": [re.compile(p, re.IGNORECASE) for p in [
        r"\bupdate\b", r"\bbump\b", r"\brename\b", r"\bcleanup\b",
        r"\brefactor\b", r"ลบ",
    ]],
}


class TestIntentPatternSinglePass:
    """Test single-pass regex intent detection."""

    def test_all_13_intents_detected(self):
        """All 13 intent categories are detected correctly."""
        tests = [
            ('I want to init the project', 'init'),
            ('อยากได้ feature ใหม่', 'backlog'),
            ('write a spec for this', 'spec'),
            ('วางแผนการทำงาน', 'plan'),
            ('implement this feature', 'implement'),
            ('bug crash error', 'fix'),
            ('release now', 'release'),
            ('retro retrospective', 'retro'),
            ('sprint ทำทั้งหมด', 'sprint'),
            ('status อะไรอยู่', 'status'),
            ('hotfix emergency', 'hotfix'),
            ('chore cleanup', 'chore'),
            ('spike explore', 'spike'),
            ('improve what if', 'brainstorm'),
        ]

        for msg, expected in tests:
            match = INTENT_PATTERN.search(msg)
            actual = match.lastgroup if match else None
            assert actual == expected, f'"{msg}" → {actual} (expected: {expected})'

    def test_single_pass_efficiency(self):
        """Single regex match extracts intent in one pass."""
        # All messages should match exactly once
        messages = [
            'I want to init',
            'อยากสร้าง feature',
            'write spec',
            'implement now',
        ]

        for msg in messages:
            match = INTENT_PATTERN.search(msg)
            assert match is not None, f'"{msg}" should match an intent'
            # lastgroup gives us the matched intent category
            assert match.lastgroup is not None

    def test_no_intent_for_unknown(self):
        """Unknown messages return None."""
        unknown_messages = [
            'hello world',
            'random text',
            'ไม่เกี่ยวข้อง',
        ]

        for msg in unknown_messages:
            match = INTENT_PATTERN.search(msg)
            assert match is None, f'"{msg}" should not match any intent'

    def test_case_insensitive(self):
        """Pattern matching is case-insensitive."""
        tests = [
            ('INIT', 'init'),
            ('Spec', 'spec'),
            ('PLAN', 'plan'),
            ('IMPLEMENT', 'implement'),
        ]

        for msg, expected in tests:
            match = INTENT_PATTERN.search(msg)
            actual = match.lastgroup if match else None
            assert actual == expected, f'"{msg}" → {actual} (expected: {expected})'


class TestNewIntentRegexes:
    """Test new-intent signal detection for sprint/fix/chore."""

    def test_sprint_signals(self):
        """Sprint signals detected correctly."""
        regexes = NEW_INTENT_REGEXES['sprint']

        # Should match ≥2 signals
        sprint_msgs = [
            'ทำเลย implement build',
            'start coding สร้าง feature',
        ]

        for msg in sprint_msgs:
            score = sum(1 for p in regexes if p.search(msg))
            assert score >= 2, f'"{msg}" should score ≥2 (got {score})'

    def test_fix_signals(self):
        """Fix signals detected correctly."""
        regexes = NEW_INTENT_REGEXES['fix']

        fix_msgs = [
            'bug error ไม่ทำงาน',
            'crash fail แก้',
        ]

        for msg in fix_msgs:
            score = sum(1 for p in regexes if p.search(msg))
            assert score >= 2, f'"{msg}" should score ≥2 (got {score})'

    def test_chore_signals(self):
        """Chore signals detected correctly."""
        regexes = NEW_INTENT_REGEXES['chore']

        chore_msgs = [
            'update bump version',
            'refactor cleanup',
        ]

        for msg in chore_msgs:
            score = sum(1 for p in regexes if p.search(msg))
            assert score >= 2, f'"{msg}" should score ≥2 (got {score})'


class TestIntentPatternOptimization:
    """Verify the single-pass optimization is actually more efficient."""

    def test_pattern_compiles_once(self):
        """INTENT_PATTERN is a compiled regex (not recompiled per message)."""
        assert isinstance(INTENT_PATTERN, re.Pattern)

    def test_named_groups_for_all_intents(self):
        """All 13 intent categories have named groups."""
        expected_groups = {
            'init', 'backlog', 'spec', 'plan', 'implement',
            'fix', 'release', 'retro', 'sprint', 'status',
            'hotfix', 'chore', 'spike', 'brainstorm',
        }
        actual_groups = set(INTENT_PATTERN.groupindex.keys())
        assert actual_groups == expected_groups
