"""Tests verifying that BLOCKS/WARNS patterns are precompiled in utils.py."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

import utils  # noqa: E402


def test_compiled_blocks_are_patterns():
    assert all(
        isinstance(p, re.Pattern) for p, _ in utils.COMPILED_BLOCKS
    ), "COMPILED_BLOCKS must contain compiled re.Pattern objects"


def test_compiled_warns_are_patterns():
    assert all(
        isinstance(p, re.Pattern) for p, _ in utils.COMPILED_WARNS
    ), "COMPILED_WARNS must contain compiled re.Pattern objects"


def test_compiled_blocks_count_matches_blocks():
    assert len(utils.COMPILED_BLOCKS) == len(utils.BLOCKS), (
        "COMPILED_BLOCKS count must match BLOCKS"
    )


def test_compiled_warns_count_matches_warns():
    assert len(utils.COMPILED_WARNS) == len(utils.WARNS), (
        "COMPILED_WARNS count must match WARNS"
    )


def test_ignorecase_flag_on_compiled_blocks():
    for p, _ in utils.COMPILED_BLOCKS:
        assert p.flags & re.IGNORECASE, (
            f"COMPILED_BLOCKS pattern {p.pattern!r} missing re.IGNORECASE flag"
        )


def test_ignorecase_flag_on_compiled_warns():
    for p, _ in utils.COMPILED_WARNS:
        assert p.flags & re.IGNORECASE, (
            f"COMPILED_WARNS pattern {p.pattern!r} missing re.IGNORECASE flag"
        )
