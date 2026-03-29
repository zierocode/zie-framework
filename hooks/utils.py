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

CONFIG_SCHEMA: dict = {
    "subprocess_timeout_s": (5, int),
    "safety_agent_timeout_s": (30, int),
    "auto_test_max_wait_s": (15, int),
    "auto_test_timeout_ms": (30000, int),
}


def validate_config(config: dict) -> dict:
    """Fill all CONFIG_SCHEMA keys with typed defaults.

    Missing keys → filled with schema default (no warning).
    Wrong-type keys → replaced with schema default (warning emitted).
    None input → treated as {}.
    Returns a new dict with all schema keys guaranteed present and correctly typed.
    """
    if config is None:
        config = {}
    result = dict(config)
    wrong_type_keys = []
    for key, (default, expected_type) in CONFIG_SCHEMA.items():
        if key not in result:
            result[key] = default
        elif not isinstance(result[key], expected_type):
            wrong_type_keys.append(key)
            result[key] = default
    if wrong_type_keys:
        print(
            f"[zie-framework] config: defaulted keys: {', '.join(wrong_type_keys)}",
            file=sys.stderr,
        )
    return result


CONFIG_DEFAULTS: dict = {
    "safety_check_mode": "regex",
    "test_runner": "",
    "auto_test_debounce_ms": 3000,
    "auto_test_timeout_ms": 30000,
    "test_indicators": "",
    "project_type": "unknown",
    "zie_memory_enabled": False,
}

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
    Accepts Path or str. Delegates to parse_roadmap_section_content.
    """
    path = Path(roadmap_path)
    if not path.exists():
        return []
    return parse_roadmap_section_content(path.read_text(), section_name)


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


def get_cached_adrs(
    session_id: str,
    decisions_dir,
    tmp_dir=None,
) -> "str | None":
    """Return cached ADR content if stored mtime matches current max mtime.

    decisions_dir: Path or str pointing to zie-framework/decisions/.
    tmp_dir: override tempfile.gettempdir() (test injection point).
    Returns None on cache miss, mtime mismatch, empty/missing dir, or any error.
    """
    try:
        decisions_path = Path(decisions_dir)
        adr_files = list(decisions_path.glob("*.md"))
        if not adr_files:
            return None
        current_max_mtime = max(f.stat().st_mtime for f in adr_files)
        base = Path(tmp_dir) if tmp_dir else Path(tempfile.gettempdir())
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
        cache_path = base / f"zie-{safe_id}" / "adr-cache.json"
        if not cache_path.exists():
            return None
        data = json.loads(cache_path.read_text())
        if abs(data["mtime"] - current_max_mtime) > 0.001:
            return None
        return data["content"]
    except Exception:
        return None


def write_adr_cache(
    session_id: str,
    content: str,
    decisions_dir,
    tmp_dir=None,
) -> bool:
    """Write ADR content to session cache keyed by max mtime of decisions_dir.

    decisions_dir: Path or str pointing to zie-framework/decisions/.
    tmp_dir: override tempfile.gettempdir() (test injection point).
    Returns True on success, False if decisions_dir is empty/missing or write fails.
    """
    try:
        decisions_path = Path(decisions_dir)
        adr_files = list(decisions_path.glob("*.md"))
        if not adr_files:
            return False
        max_mtime = max(f.stat().st_mtime for f in adr_files)
        base = Path(tmp_dir) if tmp_dir else Path(tempfile.gettempdir())
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
        cache_dir = base / f"zie-{safe_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / "adr-cache.json"
        payload = json.dumps({"mtime": max_mtime, "content": content})
        return safe_write_tmp(cache_path, payload)
    except Exception:
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
    urllib.request.urlopen(req, timeout=timeout)  # nosec B310


def load_config(cwd: Path) -> dict:
    """Read zie-framework/.config as JSON and return a validated dict.

    Merges CONFIG_DEFAULTS first, then loaded values, then validates CONFIG_SCHEMA
    keys for type safety. Always returns a fully-typed dict with all known keys.
    Absent file returns all defaults silently. Parse errors logged to stderr.
    """
    config_path = cwd / "zie-framework" / ".config"
    try:
        raw = json.loads(config_path.read_text())
        if not isinstance(raw, dict):
            raise TypeError(f"config must be a JSON object, got {type(raw).__name__}")
        merged = {**CONFIG_DEFAULTS, **raw}
        return validate_config(merged)
    except FileNotFoundError:
        return validate_config(dict(CONFIG_DEFAULTS))
    except Exception as e:
        print(f"[zie-framework] config parse error: {e}", file=sys.stderr)
        return validate_config(dict(CONFIG_DEFAULTS))


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


def compact_roadmap_done(
    roadmap_path,
    threshold: int = 20,
    cutoff_months: int = 6,
    archive_base=None,
):
    """Compact the Done section of ROADMAP.md by archiving old entries.

    When entry count > threshold and some entries are older than cutoff_months,
    archives those entries to a Markdown file under archive_base and replaces
    them with a single summary line.

    Returns:
        (was_compacted: bool, old_entry_count: int, version_range: str)
        On no-op: (False, 0, "")

    Accepts str or Path for roadmap_path and archive_base.
    """
    import datetime as _dt

    path = Path(roadmap_path)
    if not path.exists():
        return (False, 0, "")

    raw = path.read_text()
    lines = raw.splitlines(keepends=True)

    # 1. Extract Done section boundaries
    done_start = None
    done_end = None
    for idx, line in enumerate(lines):
        if line.startswith("##") and "done" in line.lower() and done_start is None:
            done_start = idx + 1
            continue
        if line.startswith("##") and done_start is not None and done_end is None:
            done_end = idx
            break
    if done_start is None:
        return (False, 0, "")
    if done_end is None:
        done_end = len(lines)

    done_lines = lines[done_start:done_end]

    # 2. Separate entry types
    _ARCHIVE_RE = re.compile(r"^\s*-\s+\[archive\]", re.IGNORECASE)
    _ENTRY_RE = re.compile(r"^\s*-\s+\[")
    _DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

    existing_archive_lines = []
    normal_entries = []

    for line in done_lines:
        stripped = line.rstrip("\n")
        if not stripped.strip():
            continue
        if _ARCHIVE_RE.match(stripped):
            existing_archive_lines.append(stripped)
            continue
        if _ENTRY_RE.match(stripped):
            m = _DATE_RE.search(stripped)
            if m:
                try:
                    parsed = _dt.date.fromisoformat(m.group(1))
                    normal_entries.append((stripped, parsed))
                except ValueError:
                    print(
                        f"[zie-framework] compact_roadmap_done: skipping malformed date: {stripped!r}",
                        file=sys.stderr,
                    )
                    normal_entries.append((stripped, None))
            else:
                normal_entries.append((stripped, None))

    if len(normal_entries) <= threshold:
        return (False, 0, "")

    # 3. Identify old entries
    today = _dt.date.today()
    cutoff = today - _dt.timedelta(days=cutoff_months * 30)
    old_entries = [(l, d) for l, d in normal_entries if d is not None and d < cutoff]

    if not old_entries:
        return (False, 0, "")

    # 4. Derive version range
    _VERSION_RE = re.compile(r"v(\d+\.\d+(?:\.\d+)?)")
    versions = []
    dates_found = []
    for line, d in old_entries:
        vm = _VERSION_RE.search(line)
        if vm:
            versions.append(vm.group(0))
        if d:
            dates_found.append(d)

    if versions:
        v_start = versions[-1]
        v_end = versions[0]
        version_range = f"{v_start}-{v_end}"
        label = f"{v_start}\u2013{v_end}"
    else:
        version_range = "unknown"
        label = "unknown"

    if dates_found:
        d_start = min(dates_found).strftime("%Y-%m")
        d_end = max(dates_found).strftime("%Y-%m")
        date_range_label = f"{d_start} to {d_end}"
    else:
        date_range_label = "unknown"

    n_old = len(old_entries)

    # 5. Resolve archive_base
    if archive_base is None:
        archive_dir = path.parent / "zie-framework" / "archive"
    else:
        archive_dir = Path(archive_base)
    archive_dir.mkdir(parents=True, exist_ok=True)

    # 6. Write archive file
    safe_range = re.sub(r"[^a-zA-Z0-9._-]", "-", version_range)
    archive_path = archive_dir / f"ROADMAP-{safe_range}.md"
    archive_content = (
        f"# ROADMAP Archive \u2014 {label} ({date_range_label})\n\n"
        f"Archived by compact_roadmap_done on {today.isoformat()}.\n"
        f"{n_old} entries older than {cutoff_months} months.\n\n"
        + "\n".join(line for line, _ in old_entries)
        + "\n"
    )
    atomic_write(archive_path, archive_content)

    # 7. Build summary line
    archive_rel = str(archive_path).replace(str(path.parent) + "/", "")
    summary_line = (
        f"- [archive] {label} ({date_range_label}): "
        f"{n_old} features shipped \u2014 see {archive_rel}"
    )

    # 8. Rebuild Done section
    old_entry_lines = {line for line, _ in old_entries}
    kept_normal = [line for line, d in normal_entries if line not in old_entry_lines]

    new_done_lines = (
        [summary_line + "\n"]
        + [l + "\n" for l in existing_archive_lines]
        + [l + "\n" for l in kept_normal]
    )

    new_lines = (
        lines[:done_start]
        + ["\n"]
        + new_done_lines
        + ["\n"]
        + lines[done_end:]
    )

    atomic_write(path, "".join(new_lines))
    return (True, n_old, version_range)
