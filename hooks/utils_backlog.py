#!/usr/bin/env python3
"""Backlog intelligence helpers — auto-tag and duplicate detection."""
from pathlib import Path


def infer_tag(title: str, keyword_map: dict) -> str:
    """Infer a tag from title text using keyword_map.

    keyword_map: {tag: [keyword, ...]} — first match wins.
    Matching is case-insensitive substring. Default tag is 'feature'.
    """
    title_lower = title.lower()
    for tag, keywords in keyword_map.items():
        for kw in keywords:
            if kw.lower() in title_lower:
                return tag
    return "feature"


def find_duplicate_slugs(new_slug: str, backlog_dir) -> list:
    """Return list of existing slugs with ≥2 token overlap against new_slug.

    backlog_dir: Path to directory containing backlog *.md files.
    Tokens: split slug by '-', lowercase. Exact self-match is excluded.
    Returns [] when backlog_dir is empty or missing.
    """
    backlog_path = Path(backlog_dir)
    if not backlog_path.exists():
        return []
    new_tokens = set(new_slug.lower().split("-"))
    duplicates = []
    for f in backlog_path.glob("*.md"):
        existing_slug = f.stem
        if existing_slug == new_slug:
            continue
        existing_tokens = set(existing_slug.lower().split("-"))
        if len(new_tokens & existing_tokens) >= 2:
            duplicates.append(existing_slug)
    return duplicates
