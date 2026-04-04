"""Structural test: zie-implement must use adr_cache_path in context bundle."""
from pathlib import Path

ZIE_IMPLEMENT = Path(__file__).parents[2] / "commands" / "implement.md"


def test_context_bundle_references_adr_cache_path():
    assert "adr_cache_path" in ZIE_IMPLEMENT.read_text()


def test_context_bundle_references_write_adr_cache():
    assert "write_adr_cache" in ZIE_IMPLEMENT.read_text()
