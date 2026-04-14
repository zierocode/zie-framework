#!/usr/bin/env python3
"""SessionStart hook — inject current SDLC state for instant session orientation."""
import json
import os
import re
import subprocess
import sys
import time as _time
from pathlib import Path

_hook_start = _time.monotonic()

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, log_hook_timing, read_event  # noqa: E402
from utils_config import load_config, CACHE_TTLS
from utils_cache import get_cache_manager  # noqa: E402
from utils_roadmap import parse_roadmap_now, is_mtime_fresh, parse_roadmap_section, parse_roadmap_section_content
from zie_context_loader import get_cached_context  # noqa: E402

# Minimum safe Playwright version — derived from CVE-2025-59288.
# CVE-2025-59288: arbitrary code execution via malicious CDP response.
# Reference: https://www.cve.org/CVERecord?id=CVE-2025-59288
# (1, 55, 1) is the first Playwright release that ships the fix.
PLAYWRIGHT_MIN_VERSION = (1, 55, 1)


def _check_playwright_version(config: dict) -> None:
    """Warn and disable playwright_enabled if installed version is below minimum safe."""
    if not config.get("playwright_enabled"):
        return

    raw = ""
    try:
        result = subprocess.run(
            ["playwright", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        raw = result.stdout.strip()
        parts = raw.split()
        version_str = parts[-1] if parts else ""
        version_tuple = tuple(int(x) for x in version_str.split(".") if x)
        if not version_tuple:
            raise ValueError("empty version")
        if version_tuple < PLAYWRIGHT_MIN_VERSION:
            min_str = ".".join(str(x) for x in PLAYWRIGHT_MIN_VERSION)
            print(
                f"[zie-framework] WARNING: Playwright {version_str} is below minimum safe"
                f" version {min_str} (CVE-2025-59288). playwright_enabled disabled for this"
                f" session. Run: playwright self-update",
                file=sys.stderr,
            )
            config["playwright_enabled"] = False
    except (FileNotFoundError, OSError):
        print(
            "[zie-framework] WARNING: playwright not found."
            " playwright_enabled disabled for this session.",
            file=sys.stderr,
        )
        config["playwright_enabled"] = False
    except ValueError:
        print(
            f"[zie-framework] session-resume: could not parse playwright version from: \"{raw}\"",
            file=sys.stderr,
        )
    except Exception as e:
        print(
            f"[zie-framework] session-resume: playwright version check failed: {e}",
            file=sys.stderr,
        )


# Outer guard — any unhandled exception exits 0 (never blocks Claude)
try:
    event = read_event()

    cwd = get_cwd()
    zf = cwd / "zie-framework"

    if not zf.exists():
        print("[zie-framework] init: project not set up — run /init to initialize zie-framework")
        sys.exit(0)

    # Read config
    config = load_config(cwd)

    # Playwright version safety check (CVE-2025-59288)
    _check_playwright_version(config)

    # Read ROADMAP via unified cache (session-scoped)
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    roadmap_file = zf / "ROADMAP.md"
    cache = get_cache_manager(cwd)
    roadmap_ttl = CACHE_TTLS.get("roadmap", 600)
    roadmap_content = cache.get_or_compute(
        "roadmap", session_id, lambda: roadmap_file.read_text(), roadmap_ttl
    )
    now_items = parse_roadmap_section_content(roadmap_content, "now") if roadmap_content else []

    # Read VERSION
    version = "?"
    version_file = cwd / "VERSION"
    if version_file.exists():
        version = version_file.read_text().strip()

    project_name = cwd.name
    project_type = config.get("project_type")
    zie_memory = config.get("zie_memory_enabled")

    # Write config vars to CLAUDE_ENV_FILE (SessionStart env injection)
    _env_file_path = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if _env_file_path:
        try:
            _debounce_ms = "3000"
            try:
                _debounce_ms = str(int(config.get("auto_test_debounce_ms")))
            except (TypeError, ValueError):
                _debounce_ms = "3000"
            _env_lines = (
                f"export ZIE_PROJECT='{project_name}'\n"
                f"export ZIE_TEST_RUNNER='{config.get('test_runner')}'\n"
                f"export ZIE_MEMORY_ENABLED='{'1' if zie_memory else '0'}'\n"
                f"export ZIE_AUTO_TEST_DEBOUNCE_MS='{_debounce_ms}'\n"
            )
            _p = Path(_env_file_path)
            if os.path.islink(_p):
                print(
                    f"[zie-framework] WARNING: CLAUDE_ENV_FILE is a symlink,"
                    f" skipping write: {_p}",
                    file=sys.stderr,
                )
                sys.exit(0)
            _p.write_text(_env_lines)
            os.chmod(_p, 0o600)
        except Exception as e:
            print(
                f"[zie-framework] session-resume: env-file write failed: {e}",
                file=sys.stderr,
            )

    # Active feature: first Now item, or fallback message
    if now_items:
        active_label = now_items[0]
    else:
        active_label = "No active feature — run /backlog to start one"

    lines = [
        f"[zie-framework] {project_name} ({project_type}) v{version}",
        f"  Active: {active_label}",
        f"  Brain: {'enabled' if zie_memory else 'disabled'}",
        "  → Run /status for full state",
    ]

    print("\n".join(lines))

    # ── Session continuity snapshot (from .remember/now.md) ───────────────────
    try:
        now_buf = cwd / ".remember" / "now.md"
        if now_buf.is_file():
            buf_text = now_buf.read_text().strip()
            if buf_text:
                # Extract first meaningful content line (skip headings + blanks)
                snippet = ""
                for line in buf_text.splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        snippet = stripped[:120]
                        break
                if snippet:
                    print(f"[zie-framework] Last session: {snippet}")
    except Exception as _e:
        if not isinstance(_e, (IsADirectoryError, PermissionError)):
            print(f"[zie-framework] session-resume: continuity read skipped: {_e}", file=sys.stderr)

    # ── Framework self-awareness block ────────────────────────────────────────

    # Staleness check: warn if PROJECT.md older than latest git commit
    try:
        project_md_mtime = (zf / "PROJECT.md").stat().st_mtime
        git_commit_mtime = float(
            subprocess.check_output(
                ["git", "log", "-1", "--format=%ct"], cwd=str(cwd)
            ).decode().strip()
        )
        # is_mtime_fresh(max_mtime, written_at): True when max_mtime <= written_at
        # max_mtime=git_commit_mtime, written_at=project_md_mtime → True = fresh
        stale = not is_mtime_fresh(git_commit_mtime, project_md_mtime)
        if stale:
            print("[zie-framework] knowledge: PROJECT.md outdated — run /resync to refresh")
    except Exception as _e:
        if not isinstance(_e, FileNotFoundError):
            print(f"[zie-framework] session-resume: staleness check skipped: {_e}", file=sys.stderr)

    # Load command map from unified cache (invalidate on SKILL.md mtime change)
    _HARDCODED_FALLBACK = (
        "[zie-framework] framework: commands — "
        "/backlog /spec /plan /implement /sprint /fix /chore /hotfix "
        "/guide /status /audit /retro /release /resync /init"
    )
    try:
        context = get_cached_context(cwd)
        cmd_line = f"[zie-framework] framework: commands — {' '.join(c['name'] for c in context['commands'])}"
    except Exception:
        cmd_line = _HARDCODED_FALLBACK

    print(cmd_line)
    print("[zie-framework] workflow: backlog→spec→plan→implement→release→retro (use /sprint for full pipeline)")
    print("[zie-framework] anti-patterns: never approve spec/plan directly; always run reviewer first; never skip pipeline on \"ทำเลย\"")

    # Backlog nudge: Next lane items pending
    try:
        next_items = parse_roadmap_section(roadmap_file, "next")
        if next_items:
            print(
                f"[zie-framework] backlog: {len(next_items)} item(s) pending"
                f" — run /spec {next_items[0]} to start designing"
            )
    except Exception as _e:
        print(f"[zie-framework] session-resume: backlog nudge skipped: {_e}", file=sys.stderr)

    # Drift detection — fire-and-forget background check
    try:
        import subprocess as _sp
        _kh_script = os.environ.get(
            "ZIE_KNOWLEDGE_HASH_SCRIPT",
            os.path.join(os.path.dirname(__file__), "knowledge-hash.py"),
        )
        _sp.Popen(
            [sys.executable, _kh_script, "--check", "--root", str(cwd)],
            stdout=_sp.DEVNULL,
            stderr=_sp.DEVNULL,
        )
    except Exception as e:
        print(f"[zie-framework] session-resume: drift check failed: {e}", file=sys.stderr)

    # ── Auto-Improve: Load and auto-apply high-confidence patterns ────────────
    try:
        from utils_io import atomic_write

        def _load_pending_patterns():
            """Load pending patterns from session memory files."""
            memory_dir = zf / "memory"
            patterns = []
            if memory_dir.exists():
                for f in memory_dir.glob("session-*.json"):
                    try:
                        data = json.loads(f.read_text())
                        for pattern in data.get("patterns", []):
                            if pattern.get("auto_apply", False):
                                patterns.append(pattern)
                    except Exception:
                        pass
            return patterns

        def _filter_auto_apply_patterns(patterns):
            """Filter patterns eligible for auto-apply."""
            _AUTO_APPLY_CATEGORIES = {"workflow", "decision"}
            _AUTO_APPLY_THRESHOLD = 0.95
            eligible = []
            for p in patterns:
                confidence = p.get("confidence", 0)
                category = p.get("category", "")
                if confidence >= _AUTO_APPLY_THRESHOLD and category in _AUTO_APPLY_CATEGORIES:
                    eligible.append(p)
            return eligible

        def _apply_pattern_to_memory(pattern, memory_path):
            """Apply a pattern to MEMORY.md."""
            if not memory_path.exists():
                return False
            content = memory_path.read_text()
            if pattern["description"] in content:
                return True
            patterns_section = re.search(r'^## Patterns\s*$', content, re.MULTILINE)
            if patterns_section:
                insert_pos = patterns_section.end()
                pattern_entry = f"\n- [{pattern['category'].upper()}] {pattern['description']} (confidence: {pattern['confidence']})\n"
                new_content = content[:insert_pos] + pattern_entry + content[insert_pos:]
            else:
                references_section = re.search(r'^## References\s*$', content, re.MULTILINE)
                if references_section:
                    insert_pos = references_section.start()
                    new_content = content[:insert_pos] + f"\n## Patterns\n\n- [{pattern['category'].upper()}] {pattern['description']} (confidence: {pattern['confidence']})\n\n" + content[insert_pos:]
                else:
                    new_content = content + f"\n\n## Patterns\n\n- [{pattern['category'].upper()}] {pattern['description']} (confidence: {pattern['confidence']})\n"
            try:
                atomic_write(memory_path, new_content)
                return True
            except Exception:
                return False

        def _load_pending_learn_marker():
            """Load pending_learn.txt marker from previous session."""
            marker = zf / "pending_learn.txt"
            if not marker.exists():
                return None
            try:
                lines = marker.read_text().strip().splitlines()
                data = {}
                for line in lines:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        data[key.strip()] = value.strip()
                return data
            except Exception:
                return None

        # Load pending learn marker
        pending_data = _load_pending_learn_marker()

        # Load and filter patterns
        patterns = _load_pending_patterns()
        eligible_patterns = _filter_auto_apply_patterns(patterns)

        # Auto-apply eligible patterns
        applied = []
        memory_path = zf / "memory" / "MEMORY.md"
        for pattern in eligible_patterns:
            if _apply_pattern_to_memory(pattern, memory_path):
                applied.append(pattern)

        # Build auto-improve context injection
        if applied or (pending_data and pending_data.get("wip")):
            auto_improve_lines = ["## Auto-Improve Session Resume"]
            if pending_data and pending_data.get("wip"):
                auto_improve_lines.append(f"\n**WIP from last session:** {pending_data['wip'][:100]}")
            if applied:
                auto_improve_lines.append(f"\n**Auto-applied {len(applied)} high-confidence pattern(s):**")
                for p in applied[:3]:
                    auto_improve_lines.append(f"- [{p['category']}] {p['description']}")

            # Output via additionalContext for SessionStart
            print(json.dumps({"additionalContext": "\n".join(auto_improve_lines)}))

        # Clean up pending marker after processing
        pending_marker = zf / "pending_learn.txt"
        if pending_marker.exists():
            try:
                pending_marker.unlink()
            except Exception:
                pass

    except Exception as _e:
        print(f"[zie-framework] session-resume: auto-improve skipped: {_e}", file=sys.stderr)

except Exception:
    sys.exit(0)

log_hook_timing(
    "session-resume",
    int((_time.monotonic() - _hook_start) * 1000),
    0,
    session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
)
