#!/usr/bin/env python3
"""File I/O helpers (tmp + persistent storage tiers) for zie-framework hooks."""

import os
import re
import sys
import tempfile
from pathlib import Path


def safe_project_name(project: str) -> str:
    """Sanitize a project name to alphanumeric-and-dash only.

    Single source of truth for the sanitization rule used in tmp paths and
    session-cleanup globs. Replaces any non-alphanumeric character with '-'.
    """
    return re.sub(r"[^a-zA-Z0-9]", "-", project)


def project_tmp_path(name: str, project: str) -> Path:
    """Return a project-scoped tmp path to prevent cross-project collisions.

    Uses tempfile.gettempdir() for portability (resolves Bandit B108).
    """
    return Path(tempfile.gettempdir()) / f"zie-{safe_project_name(project)}-{name}"


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
            "[zie-framework] CLAUDE_PLUGIN_DATA not set, using tempfile.gettempdir() fallback",
            file=sys.stderr,
        )
        path = Path(tempfile.gettempdir()) / f"zie-{safe_project_name(project)}-persistent"
    path.mkdir(parents=True, exist_ok=True)
    return path


def persistent_project_path(name: str, project: str) -> Path:
    """Return a project-scoped persistent path under CLAUDE_PLUGIN_DATA.

    Mirrors project_tmp_path() but uses get_plugin_data_dir() instead of /tmp.
    Example: persistent_project_path("edit-count", "my-proj")
             -> Path("<CLAUDE_PLUGIN_DATA>/my-proj/edit-count")
    """
    return get_plugin_data_dir(project) / name


def is_zie_initialized(cwd: Path) -> bool:
    """Return True if cwd contains a zie-framework directory (not just a file)."""
    return (cwd / "zie-framework").is_dir()


def get_project_name(cwd: Path) -> str:
    """Return sanitized project name derived from directory name."""
    return safe_project_name(cwd.name)


def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically using an unpredictable temp file and rename.

    Uses tempfile.NamedTemporaryFile to avoid predictable sibling names and
    eliminate the TOCTOU window. Sets owner-only (0o600) permissions on the
    final file after rename.
    """
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False, suffix=".tmp") as f:
        f.write(content)
        tmp_name = f.name
    try:
        os.replace(tmp_name, path)
        os.chmod(path, 0o600)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def safe_write_tmp(path: Path, content: str) -> bool:
    """Atomically write content to path, refusing to follow symlinks.

    Uses NamedTemporaryFile for an unpredictable intermediate name. Sets
    owner-only (0o600) permissions on the final file. Returns True on success,
    False if path is a symlink or an OSError occurs.
    """
    if os.path.islink(path):
        print(
            f"[zie-framework] WARNING: tmp path is a symlink, skipping write: {path}",
            file=sys.stderr,
        )
        return False
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False, suffix=".tmp") as f:
            f.write(content)
            tmp_name = f.name
        os.replace(tmp_name, path)
        os.chmod(path, 0o600)
        return True
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        return False


def safe_write_persistent(path: Path, content: str) -> bool:
    """Atomically write content to a persistent path, refusing to follow symlinks.

    Uses NamedTemporaryFile for an unpredictable intermediate name. Sets
    owner-only (0o600) permissions on the final file. Returns True on success,
    False if path is a symlink or an OSError occurs.
    """
    if os.path.islink(path):
        print(
            f"[zie-framework] WARNING: persistent path is a symlink, skipping write: {path}",
            file=sys.stderr,
        )
        return False
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False, suffix=".tmp") as f:
            f.write(content)
            tmp_name = f.name
        os.replace(tmp_name, path)
        os.chmod(path, 0o600)
        return True
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        return False
