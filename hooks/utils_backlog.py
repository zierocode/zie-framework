#!/usr/bin/env python3
"""Backlog intelligence helpers — auto-tag and duplicate detection."""
import re
from pathlib import Path

from utils_error import log_error


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


def _tokenize(text: str) -> set:
    """Tokenize text into lowercase word set for overlap comparison."""
    return set(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def find_duplicate_slugs(new_slug: str, backlog_dir) -> list:
    """Return list of existing slugs with ≥2 token overlap against new_slug.

    backlog_dir: Path to directory containing backlog *.md files.
    Tokens: split slug by '-', lowercase. Exact self-match is excluded.
    Also checks title text from file content (# Title line).
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
        # Also include title text tokens
        try:
            content = f.read_text()
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if title_match:
                existing_tokens |= _tokenize(title_match.group(1))
        except (OSError, FileNotFoundError) as e:
            log_error("utils_backlog", "read_title", e)
        if len(new_tokens & existing_tokens) >= 2:
            duplicates.append(existing_slug)
    return duplicates


def find_roadmap_overlaps(new_title: str, roadmap_path) -> list:
    """Scan Ready and Done sections of ROADMAP for title overlap with new_title.

    Returns list of (section, title) tuples where ≥2 tokens overlap.
    """
    roadmap = Path(roadmap_path)
    if not roadmap.exists():
        return []
    new_tokens = _tokenize(new_title)
    if len(new_tokens) < 2:
        return []
    content = roadmap.read_text()
    overlaps = []
    sections = [("Ready", r"## Ready.*?\n(.*?)(?=\n---|\n## )"),
                ("Done", r"## Done.*?\n(.*?)(?=\n---|\n## |\Z)")]
    for section_name, pattern in sections:
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            continue
        block = match.group(1)
        for line in block.splitlines():
            line = line.strip()
            if not line.startswith("- ["):
                continue
            # Extract title text from ROADMAP line: - [ ] slug — title or - [x] slug — title
            title_match = re.search(r"—\s*(.+?)(?:\s+←|\s*$)", line)
            if title_match:
                existing_title = title_match.group(1).strip()
                existing_tokens = _tokenize(existing_title)
                if len(new_tokens & existing_tokens) >= 2:
                    overlaps.append((section_name, existing_title))
    return overlaps


def is_full_duplicate(new_title: str, new_slug: str, existing_slug: str, backlog_dir) -> bool:
    """Check if existing item is a full duplicate (all tokens match)."""
    new_tokens = _tokenize(new_title) | set(new_slug.lower().split("-"))
    existing_path = Path(backlog_dir) / f"{existing_slug}.md"
    if not existing_path.exists():
        return False
    try:
        content = existing_path.read_text()
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            existing_tokens = _tokenize(title_match.group(1)) | set(existing_slug.lower().split("-"))
            return new_tokens <= existing_tokens
    except (OSError, FileNotFoundError) as e:
        log_error("utils_backlog", "read_title", e)
    return False
