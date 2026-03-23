"""Shared utilities for zie-framework hooks. Not a hook — do not run directly."""
import re
import sys
from pathlib import Path


def parse_roadmap_now(roadmap_path) -> list:
    """Extract cleaned items from the ## Now section of ROADMAP.md.

    Returns [] if the file is missing, the Now section is absent, or it is empty.
    Accepts Path or str.
    """
    path = Path(roadmap_path)
    if not path.exists():
        return []
    lines = []
    in_now = False
    for line in path.read_text().splitlines():
        if line.startswith("##") and "now" in line.lower():
            in_now = True
            continue
        if line.startswith("##") and in_now:
            break
        if in_now and line.strip().startswith("- "):
            clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line.strip())
            clean = clean.lstrip("- ").lstrip("[ ]").lstrip("[x]").strip()
            if clean:
                lines.append(clean)
    return lines


def project_tmp_path(name: str, project: str) -> Path:
    """Return a project-scoped /tmp path to prevent cross-project collisions.

    Example: project_tmp_path("last-test", "my-project") -> Path("/tmp/zie-my-project-last-test")
    """
    safe_project = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return Path(f"/tmp/zie-{safe_project}-{name}")
