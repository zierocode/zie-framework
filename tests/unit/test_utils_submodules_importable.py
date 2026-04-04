"""Smoke tests: each sub-module is independently importable."""
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = "/Users/zie/Code/zie-framework"


def _import_ok(module, symbols):
    cmd = (
        f"import sys; sys.path.insert(0, 'hooks'); "
        f"from {module} import {', '.join(symbols)}; print('ok')"
    )
    r = subprocess.run([sys.executable, "-c", cmd],
                      capture_output=True, text=True,
                      cwd=REPO_ROOT)
    assert r.returncode == 0 and "ok" in r.stdout, r.stderr


def test_utils_config_importable():
    _import_ok("utils_config", ["CONFIG_SCHEMA", "CONFIG_DEFAULTS", "validate_config", "load_config"])


def test_utils_io_importable():
    _import_ok("utils_io", ["atomic_write", "safe_write_tmp", "safe_write_persistent",
                            "project_tmp_path", "get_plugin_data_dir", "persistent_project_path",
                            "is_zie_initialized", "get_project_name", "safe_project_name"])


def test_utils_roadmap_importable():
    _import_ok("utils_roadmap", ["SDLC_STAGES", "parse_roadmap_section", "parse_roadmap_section_content",
                                 "parse_roadmap_now", "parse_roadmap_ready", "read_roadmap_cached",
                                 "get_cached_roadmap", "write_roadmap_cache", "compact_roadmap_done",
                                 "get_cached_git_status", "write_git_status_cache",
                                 "get_cached_adrs", "write_adr_cache", "compute_max_mtime", "is_mtime_fresh"])


def test_utils_safety_importable():
    _import_ok("utils_safety", ["BLOCKS", "WARNS", "COMPILED_BLOCKS", "COMPILED_WARNS", "normalize_command"])


def test_utils_event_importable():
    _import_ok("utils_event", ["read_event", "get_cwd", "sanitize_log_field",
                               "log_hook_timing", "call_zie_memory_api"])


def test_no_import_from_utils_in_hooks():
    """After full migration: no hook file imports from bare 'utils'."""
    hooks_dir = Path(REPO_ROOT) / "hooks"
    violations = []
    for f in sorted(hooks_dir.glob("*.py")):
        if f.name in {"utils.py", "utils_config.py", "utils_io.py",
                      "utils_roadmap.py", "utils_safety.py", "utils_event.py"}:
            continue
        content = f.read_text()
        if re.search(r"from utils import|import utils\b", content):
            violations.append(f.name)
    assert not violations, f"Hooks still importing from bare 'utils': {violations}"


def test_group_a_hooks_no_bare_utils_import():
    """Group A hooks must not import from bare 'utils'."""
    group_a = ["safety-check.py", "safety_check_agent.py", "sdlc-permissions.py"]
    hooks_dir = Path(REPO_ROOT) / "hooks"
    violations = []
    for name in group_a:
        content = (hooks_dir / name).read_text()
        if re.search(r"from utils import|import utils\b", content):
            violations.append(name)
    assert not violations, f"Group A hooks still importing from 'utils': {violations}"


def test_group_b_hooks_no_bare_utils_import():
    import os
    group_b = ["stopfailure-log.py", "notification-log.py",
               "subagent-stop.py", "session-cleanup.py"]
    hooks_dir = Path(REPO_ROOT) / "hooks"
    violations = []
    for name in group_b:
        path = hooks_dir / name
        if not path.exists():
            continue
        content = path.read_text()
        if re.search(r"from utils import|import utils\b", content):
            violations.append(name)
    assert not violations, f"Group B hooks still importing from 'utils': {violations}"


def test_group_c_hooks_no_bare_utils_import():
    group_c = ["stop-guard.py", "task-completed-gate.py", "auto-test.py"]
    hooks_dir = Path(REPO_ROOT) / "hooks"
    violations = []
    for name in group_c:
        content = (hooks_dir / name).read_text()
        if re.search(r"from utils import|import utils\b", content):
            violations.append(name)
    assert not violations, f"Group C hooks still importing from 'utils': {violations}"


def test_group_d_hooks_no_bare_utils_import():
    group_d = ["session-resume.py", "failure-context.py", "sdlc-compact.py",
               "wip-checkpoint.py", "intent-sdlc.py", "subagent-context.py",
               "session-learn.py"]
    hooks_dir = Path(REPO_ROOT) / "hooks"
    violations = []
    for name in group_d:
        content = (hooks_dir / name).read_text()
        if re.search(r"from utils import|import utils\b", content):
            violations.append(name)
    assert not violations, f"Group D hooks still importing from 'utils': {violations}"
