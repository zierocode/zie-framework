#!/usr/bin/env python3
"""ROADMAP parsing, caching, ADR caching, and mtime gate helpers."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_error import log_error
from utils_io import atomic_write, safe_write_tmp

SDLC_STAGES: list = [
    "init",
    "backlog",
    "spec",
    "plan",
    "implement",
    "fix",
    "release",
    "retro",
]


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
            clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line.strip())
            clean = clean.lstrip("- ").lstrip("[ ]").lstrip("[x]").strip()
            if clean:
                lines.append(clean)
    return lines


def read_roadmap_cached(roadmap_path, session_id: str, cwd=None) -> str:
    """Return ROADMAP.md content using CacheManager mtime-gated cache.

    Delegates to CacheManager.get_or_compute with mtime invalidation.
    Falls back to empty string on any read error.
    """
    from utils_cache import get_cache_manager

    if cwd is None:
        cwd = Path(roadmap_path).parent.parent
    cache = get_cache_manager(cwd)
    roadmap_str = str(roadmap_path)

    def _read() -> str:
        try:
            return Path(roadmap_path).read_text()
        except OSError as e:
            log_error("utils_roadmap", "read_roadmap", e)
            return ""
        except Exception as e:
            log_error("utils_roadmap", "read_roadmap", e)
            return ""

    return cache.get_or_compute(
        "roadmap",
        session_id,
        _read,
        ttl=600,
        invalidation="mtime",
        source_path=roadmap_str,
    )


def get_cached_git_status(session_id: str, key: str, ttl: int = 5) -> str | None:
    """Return cached git output if fresh (age < ttl seconds), else None.

    key identifies the git command (e.g. 'log', 'branch', 'diff').
    Returns None on cache miss, expiry, or any read error.
    """
    try:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
        safe_key = re.sub(r"[^a-zA-Z0-9_-]", "-", key)
        cache_path = Path(tempfile.gettempdir()) / f"zie-{safe_id}" / f"git-{safe_key}.cache"
        if cache_path.exists():
            age = time.time() - cache_path.stat().st_mtime
            if age < ttl:
                return cache_path.read_text()
        return None
    except OSError as e:
        log_error("utils_roadmap", "get_cached_git_status", e)
        return None
    except Exception as e:
        log_error("utils_roadmap", "get_cached_git_status", e)
        return None


def write_git_status_cache(session_id: str, key: str, content: str) -> None:
    """Write git output to the session cache.

    key identifies the git command (e.g. 'log', 'branch', 'diff').
    """
    try:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
        safe_key = re.sub(r"[^a-zA-Z0-9_-]", "-", key)
        cache_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"git-{safe_key}.cache").write_text(content)
    except Exception as e:
        print(f"[zie-framework] write_git_status_cache: {e}", file=sys.stderr)


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
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
        cache_path = base / f"zie-{safe_id}" / "adr-cache.json"
        if not cache_path.exists():
            return None
        data = json.loads(cache_path.read_text())
        if abs(data["mtime"] - current_max_mtime) > 0.001:
            return None
        return data["content"]
    except (OSError, json.JSONDecodeError) as e:
        log_error("utils_roadmap", "get_cached_adrs", e)
        return None
    except Exception as e:
        log_error("utils_roadmap", "get_cached_adrs", e)
        return None


def write_adr_cache(
    session_id: str,
    content: str,
    decisions_dir,
    tmp_dir=None,
) -> "tuple[bool, Path | None]":
    """Write ADR content to session cache keyed by max mtime of decisions_dir.

    decisions_dir: Path or str pointing to zie-framework/decisions/.
    tmp_dir: override tempfile.gettempdir() (test injection point).
    Returns (True, cache_path) on success, (False, None) if decisions_dir is
    empty/missing or write fails.
    """
    try:
        decisions_path = Path(decisions_dir)
        adr_files = list(decisions_path.glob("*.md"))
        if not adr_files:
            return (False, None)
        max_mtime = max(f.stat().st_mtime for f in adr_files)
        base = Path(tmp_dir) if tmp_dir else Path(tempfile.gettempdir())
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
        cache_dir = base / f"zie-{safe_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / "adr-cache.json"
        payload = json.dumps({"mtime": max_mtime, "content": content})
        if safe_write_tmp(cache_path, payload):
            return (True, cache_path)
        return (False, None)
    except OSError as e:
        log_error("utils_roadmap", "write_adr_cache", e)
        return (False, None)
    except Exception as e:
        log_error("utils_roadmap", "write_adr_cache", e)
        return (False, None)


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
    old_entries = [(ln, d) for ln, d in normal_entries if d is not None and d < cutoff]

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
        f"{n_old} entries older than {cutoff_months} months.\n\n" + "\n".join(line for line, _ in old_entries) + "\n"
    )
    atomic_write(archive_path, archive_content)

    # 7. Build summary line
    archive_rel = str(archive_path).replace(str(path.parent) + "/", "")
    summary_line = f"- [archive] {label} ({date_range_label}): {n_old} features shipped \u2014 see {archive_rel}"

    # 8. Rebuild Done section
    old_entry_lines = {line for line, _ in old_entries}
    kept_normal = [line for line, d in normal_entries if line not in old_entry_lines]

    new_done_lines = (
        [summary_line + "\n"] + [ln + "\n" for ln in existing_archive_lines] + [ln + "\n" for ln in kept_normal]
    )

    new_lines = lines[:done_start] + ["\n"] + new_done_lines + ["\n"] + lines[done_end:]

    atomic_write(path, "".join(new_lines))
    return (True, n_old, version_range)


# ---------------------------------------------------------------------------
# mtime gate helpers
# ---------------------------------------------------------------------------


def compute_max_mtime(base_dir: Path, pattern: str = "*.md") -> float:
    """Return max mtime (float) of files matching pattern (glob) under base_dir.

    Returns 0.0 if no files match.
    """
    mtimes = [p.stat().st_mtime for p in base_dir.rglob(pattern)]
    return max(mtimes) if mtimes else 0.0


def is_mtime_fresh(max_mtime: float, written_at: float) -> bool:
    """Return True if max_mtime <= written_at (no file newer than last write)."""
    return max_mtime <= written_at


def parse_roadmap_items_with_dates(roadmap_path, section_name: str) -> list:
    """Extract items from a named ## section with parsed ISO dates.

    Returns a list of (item_text: str, date: datetime.date | None) tuples.
    date is the first YYYY-MM-DD found in the raw line, or None if absent.
    Returns [] if file missing, section absent, or empty.
    """
    import datetime as _dt

    _DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
    try:
        path = Path(roadmap_path)
        if not path.exists():
            return []
        content = path.read_text()
        results = []
        in_section = False
        for line in content.splitlines():
            if line.startswith("##") and section_name.lower() in line.lower():
                in_section = True
                continue
            if line.startswith("##") and in_section:
                break
            if in_section and line.strip().startswith("- "):
                clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line.strip())
                clean = clean.lstrip("- ").lstrip("[ ]").lstrip("[x]").strip()
                if not clean:
                    continue
                m = _DATE_RE.search(line)
                date = None
                if m:
                    try:
                        date = _dt.date.fromisoformat(m.group(1))
                    except ValueError:
                        date = None
                results.append((clean, date))
        return results
    except OSError as e:
        log_error("utils_roadmap", "parse_roadmap_items_with_dates", e)
        return []
    except Exception as e:
        log_error("utils_roadmap", "parse_roadmap_items_with_dates", e)
        return []


def is_track_active(cwd) -> bool:
    """Return True if any active workflow track exists.

    Checks two sources:
    1. ROADMAP.md Now lane — any open [ ] item.
    2. zie-framework/.drift-log — any NDJSON line with closed_at == null.

    Returns False (never raises) when files are missing or unreadable.
    """
    cwd = Path(cwd)
    zf = cwd / "zie-framework"

    # Source 1: Now lane open item
    try:
        roadmap_path = zf / "ROADMAP.md"
        if roadmap_path.exists():
            content = roadmap_path.read_text()
            in_now = False
            for line in content.splitlines():
                if line.startswith("##") and "now" in line.lower():
                    in_now = True
                    continue
                if line.startswith("##") and in_now:
                    break
                if in_now and re.search(r"-\s*\[\s*\]", line):
                    return True
    except OSError as e:
        log_error("utils_roadmap", "is_track_active_roadmap", e)
    except Exception as e:
        log_error("utils_roadmap", "is_track_active_roadmap", e)

    # Source 2: open drift marker
    try:
        drift_path = zf / ".drift-log"
        if drift_path.exists():
            for raw in drift_path.read_text().splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    event = json.loads(raw)
                    if event.get("closed_at") is None and "track" in event:
                        return True
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    log_error("utils_roadmap", "drift_line_parse", e)
                    continue
    except (OSError, json.JSONDecodeError) as e:
        log_error("utils_roadmap", "is_track_active_drift", e)
    except Exception as e:
        log_error("utils_roadmap", "is_track_active_drift", e)

    return False


def extract_problem_excerpt(slug: str, backlog_dir, max_len: int = 120) -> str:
    """Extract Problem excerpt from a backlog file.

    Reads backlog/<slug>.md, extracts text between ## Problem and the
    next ## heading. Truncates to max_len chars, appends … if longer.
    Returns '(no description)' if file missing or no Problem section.
    """
    backlog_path = Path(backlog_dir) / f"{slug}.md"
    if not backlog_path.exists():
        return "(no description)"
    try:
        content = backlog_path.read_text()
        match = re.search(r"^## Problem\s*\n\n(.+?)(?:\n\n## |\n\n---|\Z)", content, re.DOTALL | re.MULTILINE)
        if not match:
            return "(no description)"
        text = match.group(1).strip().replace("\n", " ")
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        if len(text) > max_len:
            return text[:max_len].rstrip() + "…"
        return text
    except OSError as e:
        log_error("utils_roadmap", "extract_problem_excerpt", e)
        return "(no description)"
    except Exception as e:
        log_error("utils_roadmap", "extract_problem_excerpt", e)
        return "(no description)"


def check_spec_plan_status(slug: str, specs_dir, plans_dir) -> tuple:
    """Check existence of spec and plan files for a slug.

    Returns (spec_exists, plan_exists) as booleans.
    """
    specs_path = Path(specs_dir)
    plans_path = Path(plans_dir)
    spec_exists = any(specs_path.glob(f"*-{slug}-design.md"))
    plan_exists = any(plans_path.glob(f"*-{slug}.md"))
    return (spec_exists, plan_exists)
