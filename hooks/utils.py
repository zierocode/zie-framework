"""Shared utilities for zie-framework hooks. Not a hook — do not run directly.

Storage tiers
-------------
Tmp paths (project_tmp_path / safe_write_tmp):
    Session-scoped state. Cleared by session-cleanup.py on Stop.
    Use for: debounce timestamps, ephemeral counters that reset each session.

Persistent paths (get_plugin_data_dir / persistent_project_path / safe_write_persistent):
    Cross-session state backed by $CLAUDE_PLUGIN_DATA (set by Claude Code).
    Falls back to tempfile.gettempdir() with a warning when the env var is absent.
    Use for: edit counters that survive restart, pending_learn markers.
"""
import json
import os
import re
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

SDLC_STAGES: list = [
    "init", "backlog", "spec", "plan",
    "implement", "fix", "release", "retro",
]


def sanitize_log_field(value: object) -> str:
    """Strip ASCII control characters from a log field value.

    Converts value to str first, then replaces chars in range
    0x00-0x1f and 0x7f with '?' to prevent log injection.
    """
    return re.sub(r'[\x00-\x1f\x7f]', '?', str(value))


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


def parse_roadmap_now(roadmap_path, warn_on_empty: bool = False) -> list:
    """Extract cleaned items from the ## Now section of ROADMAP.md.

    Returns [] if the file is missing, the Now section is absent, or it is empty.
    Accepts Path or str.

    If warn_on_empty=True and the file exists but the Now section is absent
    or empty, prints a warning to stderr.
    """
    path = Path(roadmap_path)
    items = parse_roadmap_section(path, "now")
    if warn_on_empty and path.exists() and not items:
        print(
            "[zie-framework] WARNING: ROADMAP.md Now section is empty or missing",
            file=sys.stderr,
        )
    return items


def parse_roadmap_ready(roadmap_path, warn_on_empty: bool = False) -> list:
    """Extract cleaned items from the ## Ready section of ROADMAP.md.

    Returns [] if the file is missing, the Ready section is absent, or it is empty.
    Accepts Path or str.

    If warn_on_empty=True and the file exists but the Ready section is absent
    or empty, prints a warning to stderr.
    """
    path = Path(roadmap_path)
    items = parse_roadmap_section(path, "ready")
    if warn_on_empty and path.exists() and not items:
        print(
            "[zie-framework] WARNING: ROADMAP.md Ready section is empty or missing",
            file=sys.stderr,
        )
    return items


def parse_roadmap_section_content(content: str, section_name: str) -> list:
    """Extract cleaned items from a named ## section of ROADMAP content string.

    Identical logic to parse_roadmap_section but operates on a string instead
    of a file path. Returns [] if the section is absent or empty.
    """
    lines = []
    in_section = False
    for line in content.splitlines():
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


def read_roadmap_cached(roadmap_path, session_id: str, ttl: int = 30) -> str:
    """Return ROADMAP.md content using session cache, falling back to disk read.

    On cache miss: reads from disk and writes to cache.
    On any read error: returns empty string.
    """
    cached = get_cached_roadmap(session_id, ttl=ttl)
    if cached is not None:
        return cached
    try:
        content = Path(roadmap_path).read_text()
        write_roadmap_cache(session_id, content)
        return content
    except Exception:
        return ""


def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically using an unpredictable temp file and rename.

    Uses tempfile.NamedTemporaryFile to avoid predictable sibling names and
    eliminate the TOCTOU window. Sets owner-only (0o600) permissions on the
    final file after rename.
    """
    with tempfile.NamedTemporaryFile(
        mode='w', dir=path.parent, delete=False, suffix='.tmp'
    ) as f:
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


def is_zie_initialized(cwd: Path) -> bool:
    """Return True if cwd contains a zie-framework directory (not just a file)."""
    return (cwd / "zie-framework").is_dir()


def get_project_name(cwd: Path) -> str:
    """Return sanitized project name derived from directory name."""
    return safe_project_name(cwd.name)


def safe_project_name(project: str) -> str:
    """Sanitize a project name to alphanumeric-and-dash only.

    Single source of truth for the sanitization rule used in tmp paths and
    session-cleanup globs. Replaces any non-alphanumeric character with '-'.
    """
    return re.sub(r'[^a-zA-Z0-9]', '-', project)


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
        with tempfile.NamedTemporaryFile(
            mode='w', dir=path.parent, delete=False, suffix='.tmp'
        ) as f:
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


def get_cached_roadmap(session_id: str, ttl: int = 30) -> str | None:
    """Return cached ROADMAP.md content if fresh (age < ttl seconds), else None."""
    try:
        cache_path = Path(f"/tmp/zie-{session_id}/roadmap.cache")
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < ttl:
                return cache_path.read_text()
        return None
    except Exception:
        return None


def write_roadmap_cache(session_id: str, content: str) -> None:
    """Write ROADMAP.md content to the session cache."""
    try:
        cache_dir = Path(f"/tmp/zie-{session_id}")
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "roadmap.cache").write_text(content)
    except Exception:
        pass


def get_cached_git_status(session_id: str, key: str, ttl: int = 5) -> str | None:
    """Return cached git output if fresh (age < ttl seconds), else None.

    key identifies the git command (e.g. 'log', 'branch', 'diff').
    Returns None on cache miss, expiry, or any read error.
    """
    try:
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
        safe_key = re.sub(r'[^a-zA-Z0-9_-]', '-', key)
        cache_path = Path(tempfile.gettempdir()) / f"zie-{safe_id}" / f"git-{safe_key}.cache"
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < ttl:
                return cache_path.read_text()
        return None
    except Exception:
        return None


def write_git_status_cache(session_id: str, key: str, content: str) -> None:
    """Write git output to the session cache.

    key identifies the git command (e.g. 'log', 'branch', 'diff').
    Silently ignores all errors.
    """
    try:
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
        safe_key = re.sub(r'[^a-zA-Z0-9_-]', '-', key)
        cache_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"git-{safe_key}.cache").write_text(content)
    except Exception:
        pass


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
    urllib.request.urlopen(req, timeout=timeout)  # nosec B310


def load_config(cwd: Path) -> dict:
    """Read zie-framework/.config as JSON and return a dict.

    Returns {} on any error (missing file, parse failure, permission denied).
    Logs parse errors to stderr for operator visibility (ADR-019).
    """
    config_path = cwd / "zie-framework" / ".config"
    try:
        return json.loads(config_path.read_text())
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[zie-framework] config parse error: {e}", file=sys.stderr)
        return {}


def normalize_command(cmd: str) -> str:
    """Normalize whitespace and lowercase a shell command for pattern matching."""
    return re.sub(r'\s+', ' ', cmd.strip().lower())


BLOCKS = [
    # Filesystem destruction
    (r"rm\s+-rf\s+(/\s|/\b|/$)", "rm -rf / is blocked — this would destroy the system"),
    (r"rm\s+-rf\s+~", "rm -rf ~ is blocked — this would destroy your home directory"),
    (r"rm\s+-rf\s+\.", "rm -rf . blocked — use explicit paths"),
    # Database destruction
    (r"\bdrop\s+database\b", "DROP DATABASE blocked — use migrations to remove databases"),
    (r"\bdrop\s+table\b", "DROP TABLE blocked — use alembic/migrations for schema changes"),
    (r"\btruncate\s+table\b", "TRUNCATE TABLE blocked — be explicit with user before truncating"),
    # Force push
    (r"git\s+push\s+.*--force\b", "Force push blocked — use 'git push' normally or ask Zie explicitly"),
    (r"git\s+push\s+.*-f\b", "Force push blocked — use 'git push' normally"),
    (r"git\s+push\s+.*origin\s+main\b", "Direct push to main blocked — use 'make ship' instead"),
    (r"git\s+push\s+.*origin\s+master\b", "Direct push to master blocked — use 'make ship' instead"),
    # Hard reset
    (r"git\s+reset\s+--hard\b", "git reset --hard blocked — this discards uncommitted work. Use 'git stash' instead"),
    # Skip hooks
    (r"--no-verify\b", "--no-verify blocked — hooks exist for a reason. Fix the hook failure instead"),
]

# Non-blocking notices. Do NOT add patterns already caught by BLOCKS above.
WARNS = [
    (r"docker\s+compose\s+down\s+.*--volumes\b",
     "docker compose down --volumes will delete DB data — make sure you have a backup"),
    (r"alembic\s+downgrade\b",
     "Alembic downgrade detected — verify this won't lose production data"),
]


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
        with tempfile.NamedTemporaryFile(
            mode='w', dir=path.parent, delete=False, suffix='.tmp'
        ) as f:
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
