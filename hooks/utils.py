"""Shared utilities for zie-framework hooks. Not a hook — do not run directly.

Storage tiers
-------------
/tmp paths (project_tmp_path / safe_write_tmp):
    Session-scoped state. Cleared by session-cleanup.py on Stop.
    Use for: debounce timestamps, ephemeral counters that reset each session.

Persistent paths (get_plugin_data_dir / persistent_project_path / safe_write_persistent):
    Cross-session state backed by $CLAUDE_PLUGIN_DATA (set by Claude Code).
    Falls back to /tmp with a warning when the env var is absent.
    Use for: edit counters that survive restart, pending_learn markers.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path


def parse_roadmap_section(roadmap_path, section_name: str) -> list:
    """Extract cleaned items from a named ## section of ROADMAP.md.

    section_name is matched case-insensitively against ## headers.
    Returns [] if file missing, section absent, or section empty.
    Accepts Path or str.
    """
    path = Path(roadmap_path)
    if not path.exists():
        return []
    lines = []
    in_section = False
    for line in path.read_text().splitlines():
        if line.startswith("##") and section_name.lower() in line.lower():
            in_section = True
            continue
        if line.startswith("##") and in_section:
            break
        if in_section and line.strip().startswith("- "):
            clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line.strip())
            clean = clean.lstrip("- ").lstrip("[ ]").lstrip("[x]").strip()
            if clean:
                lines.append(clean)
    return lines


def parse_roadmap_now(roadmap_path) -> list:
    """Extract cleaned items from the ## Now section of ROADMAP.md.

    Returns [] if the file is missing, the Now section is absent, or it is empty.
    Accepts Path or str.
    """
    return parse_roadmap_section(roadmap_path, "now")


def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically using a sibling .tmp file and rename.

    On POSIX, os.rename() (called by Path.rename()) is atomic at the filesystem
    level, preventing partial reads from concurrent writers.
    """
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(content)
    tmp_path.rename(path)


def safe_project_name(project: str) -> str:
    """Sanitize a project name to alphanumeric-and-dash only.

    Single source of truth for the sanitization rule used in tmp paths and
    session-cleanup globs. Replaces any non-alphanumeric character with '-'.
    """
    return re.sub(r'[^a-zA-Z0-9]', '-', project)


def project_tmp_path(name: str, project: str) -> Path:
    """Return a project-scoped /tmp path to prevent cross-project collisions.

    Example: project_tmp_path("last-test", "my-project") -> Path("/tmp/zie-my-project-last-test")
    """
    return Path(f"/tmp/zie-{safe_project_name(project)}-{name}")  # nosec B108 — project-scoped /tmp paths by design


def get_plugin_data_dir(project: str) -> Path:
    """Return the persistent data directory for a project.

    Reads $CLAUDE_PLUGIN_DATA (set by Claude Code at hook invocation time).
    If the env var is absent or empty, falls back to a /tmp path and logs a
    warning to stderr so the caller is not silently degraded.

    Always creates the directory before returning.
    """
    base = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if base:
        path = Path(base) / safe_project_name(project)
    else:
        print(
            "[zie-framework] CLAUDE_PLUGIN_DATA not set, using /tmp fallback",
            file=sys.stderr,
        )
        path = Path(f"/tmp/zie-{safe_project_name(project)}-persistent")  # nosec B108
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write_persistent(path: Path, content: str) -> bool:
    """Atomically write content to a persistent path, refusing to follow symlinks.

    Identical contract to safe_write_tmp(): returns True on success, False if
    path is a symlink or an OSError occurs. Uses os.replace() for atomicity.
    """
    if os.path.islink(path):
        print(
            f"[zie-framework] WARNING: persistent path is a symlink, skipping write: {path}",
            file=sys.stderr,
        )
        return False
    try:
        tmp_path = path.parent / (path.name + ".tmp")
        tmp_path.write_text(content)
        os.replace(tmp_path, path)
        return True
    except OSError:
        return False


def persistent_project_path(name: str, project: str) -> Path:
    """Return a project-scoped persistent path under CLAUDE_PLUGIN_DATA.

    Mirrors project_tmp_path() but uses get_plugin_data_dir() instead of /tmp.
    Example: persistent_project_path("edit-count", "my-proj")
             -> Path("<CLAUDE_PLUGIN_DATA>/my-proj/edit-count")
    """
    return get_plugin_data_dir(project) / name


def call_zie_memory_api(url: str, key: str, endpoint: str, payload: dict, timeout: int = 5) -> None:
    """POST payload as JSON to a zie-memory API endpoint. Re-raises on network error.

    Caller is responsible for URL validation (must be https://) and error handling.
    """
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{url}{endpoint}",
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=timeout)  # nosec B310 — URL validated as https:// by caller


def read_event() -> dict:
    """Read and parse the hook event from stdin.

    Exits with code 0 on any parse failure — hooks must never crash.
    """
    try:
        return json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)


def get_cwd() -> Path:
    """Return the working directory for the current Claude Code session.

    Prefers CLAUDE_CWD env var (set by Claude Code) over os.getcwd().
    """
    return Path(os.environ.get("CLAUDE_CWD", os.getcwd()))


def safe_write_tmp(path: Path, content: str) -> bool:
    """Atomically write content to path, refusing to follow symlinks.

    Returns True on success, False if path is a symlink or an OSError occurs.
    Uses write-to-.tmp-sibling then os.replace() for atomicity.
    """
    if os.path.islink(path):
        print(
            f"[zie-framework] WARNING: tmp path is a symlink, skipping write: {path}",
            file=sys.stderr,
        )
        return False
    try:
        tmp_path = path.parent / (path.name + ".tmp")
        tmp_path.write_text(content)
        os.replace(tmp_path, path)
        return True
    except OSError:
        return False
