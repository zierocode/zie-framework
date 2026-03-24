"""Tests for hooks/session-resume.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "session-resume.py")

SAMPLE_ROADMAP = """## Now
- [ ] Build the auth module

## Next
- [ ] Add OAuth provider
- [ ] Write integration tests

## Done
- [x] Setup project
"""


def run_hook(tmp_cwd=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    return subprocess.run([sys.executable, HOOK], input=json.dumps({}),
                          capture_output=True, text=True, env=env)


def make_cwd(tmp_path, config=None, roadmap=None, version=None, plans=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if config:
        (zf / ".config").write_text(json.dumps(config))
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    if version:
        (tmp_path / "VERSION").write_text(version)
    if plans:
        plans_dir = zf / "plans"
        plans_dir.mkdir()
        for name, content in plans.items():
            (plans_dir / name).write_text(content)
    return tmp_path


class TestSessionResumeHappyPath:
    def test_prints_project_name(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"project_type": "python-lib"},
                       roadmap=SAMPLE_ROADMAP, version="1.2.3")
        r = run_hook(tmp_cwd=cwd)
        assert tmp_path.name in r.stdout
        assert "[zie-framework]" in r.stdout

    def test_prints_active_feature_from_now_section(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "auth module" in r.stdout

    def test_prints_backlog_count(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "2" in r.stdout  # 2 items in Next

    def test_prints_active_plan_when_present(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP,
                       plans={"2026-03-22-my-feature.md": "# plan"})
        r = run_hook(tmp_cwd=cwd)
        assert "2026-03-22-my-feature.md" in r.stdout

    def test_brain_enabled_when_config_says_so(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"zie_memory_enabled": True}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "enabled" in r.stdout


class TestSessionResumeGracefulDegradation:
    def test_no_output_when_no_zf_dir(self, tmp_path):
        r = run_hook(tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_no_active_feature_message_when_now_empty(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] something\n"
        cwd = make_cwd(tmp_path, config={}, roadmap=roadmap)
        r = run_hook(tmp_cwd=cwd)
        assert "No active feature" in r.stdout or "/zie-backlog" in r.stdout

    def test_handles_missing_roadmap_gracefully(self, tmp_path):
        cwd = make_cwd(tmp_path, config={})  # no roadmap
        r = run_hook(tmp_cwd=cwd)
        assert r.returncode == 0
        assert "[zie-framework]" in r.stdout


class TestHookExceptionConvention:
    def test_claude_md_documents_hook_error_convention(self):
        """CLAUDE.md must contain the Hook Error Handling Convention section."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        claude_md = os.path.join(repo_root, "CLAUDE.md")
        content = open(claude_md).read()
        assert "Hook Error Handling" in content, (
            "CLAUDE.md missing 'Hook Error Handling' section — convention not documented"
        )

    def test_no_bare_pass_in_session_resume_inner_ops(self):
        """session-resume.py must not contain bare except: pass in inner operations."""
        import ast
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        src = open(os.path.join(repo_root, "hooks", "session-resume.py")).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if (
                    node.name is None
                    and len(node.body) == 1
                    and isinstance(node.body[0], ast.Pass)
                    and node.lineno > 20
                ):
                    raise AssertionError(
                        f"Bare 'except: pass' found at line {node.lineno} "
                        "in session-resume.py — inner ops must log to stderr"
                    )


class TestSessionResumeConfigParseWarning:
    def test_warns_on_corrupt_config(self, tmp_path):
        """Corrupt .config must produce a [zie] warning on stderr."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text("not valid json !!!")
        r = run_hook(tmp_cwd=tmp_path)
        assert r.returncode == 0
        assert "[zie] warning" in r.stderr, (
            f"Expected '[zie] warning' in stderr, got: {r.stderr!r}"
        )

    def test_still_prints_output_with_corrupt_config(self, tmp_path):
        """Hook must still produce normal output even with corrupt config."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        (zf / ".config").write_text("{bad json")
        r = run_hook(tmp_cwd=tmp_path)
        assert r.returncode == 0
        assert "[zie-framework]" in r.stdout

    def test_no_warning_on_valid_config(self, tmp_path):
        """Valid .config must not produce any warning."""
        cwd = make_cwd(tmp_path, config={"project_type": "python-lib"})
        r = run_hook(tmp_cwd=cwd)
        assert "[zie] warning" not in r.stderr

    def test_no_warning_when_config_missing(self, tmp_path):
        """Missing .config must not produce any warning."""
        zf = tmp_path / "zie-framework"
        zf.mkdir()
        r = run_hook(tmp_cwd=tmp_path)
        assert "[zie] warning" not in r.stderr


def run_hook_with_env_file(tmp_cwd, env_file_path=None, extra_env=None):
    """Run session-resume.py with an optional CLAUDE_ENV_FILE set."""
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_file_path is not None:
        env["CLAUDE_ENV_FILE"] = str(env_file_path)
    else:
        env.pop("CLAUDE_ENV_FILE", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps({}),
        capture_output=True, text=True, env=env,
    )


class TestSessionResumeEnvFile:
    def test_writes_four_export_lines(self, tmp_path):
        """When CLAUDE_ENV_FILE is set, four export lines must be written."""
        env_file = tmp_path / "claude_env"
        cwd = make_cwd(tmp_path / "proj", config={
            "test_runner": "pytest",
            "zie_memory_enabled": True,
            "auto_test_debounce_ms": 5000,
        }, roadmap=SAMPLE_ROADMAP)
        run_hook_with_env_file(cwd, env_file_path=env_file)
        assert env_file.exists(), "CLAUDE_ENV_FILE was not created"
        content = env_file.read_text()
        assert "export ZIE_PROJECT=" in content
        assert "export ZIE_TEST_RUNNER=" in content
        assert "export ZIE_MEMORY_ENABLED=" in content
        assert "export ZIE_AUTO_TEST_DEBOUNCE_MS=" in content

    def test_correct_values_written(self, tmp_path):
        """Written values must match config entries."""
        env_file = tmp_path / "claude_env"
        proj_dir = tmp_path / "myproject"
        cwd = make_cwd(proj_dir, config={
            "test_runner": "pytest",
            "zie_memory_enabled": True,
            "auto_test_debounce_ms": 5000,
        }, roadmap=SAMPLE_ROADMAP)
        run_hook_with_env_file(cwd, env_file_path=env_file)
        content = env_file.read_text()
        assert "ZIE_PROJECT='myproject'" in content
        assert "ZIE_TEST_RUNNER='pytest'" in content
        assert "ZIE_MEMORY_ENABLED='1'" in content
        assert "ZIE_AUTO_TEST_DEBOUNCE_MS='5000'" in content

    def test_memory_disabled_writes_zero(self, tmp_path):
        """zie_memory_enabled=False must produce ZIE_MEMORY_ENABLED='0'."""
        env_file = tmp_path / "claude_env"
        cwd = make_cwd(tmp_path / "proj2", config={
            "zie_memory_enabled": False,
        }, roadmap=SAMPLE_ROADMAP)
        run_hook_with_env_file(cwd, env_file_path=env_file)
        content = env_file.read_text()
        assert "ZIE_MEMORY_ENABLED='0'" in content

    def test_defaults_when_config_missing(self, tmp_path):
        """Missing .config must produce default values in env file."""
        env_file = tmp_path / "claude_env"
        cwd = make_cwd(tmp_path / "proj3", roadmap=SAMPLE_ROADMAP)
        run_hook_with_env_file(cwd, env_file_path=env_file)
        content = env_file.read_text()
        assert "ZIE_TEST_RUNNER=''" in content
        assert "ZIE_MEMORY_ENABLED='0'" in content
        assert "ZIE_AUTO_TEST_DEBOUNCE_MS='3000'" in content

    def test_no_write_when_claude_env_file_absent(self, tmp_path):
        """No CLAUDE_ENV_FILE set — hook must exit 0 and write nothing."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"}, roadmap=SAMPLE_ROADMAP)
        r = run_hook_with_env_file(cwd, env_file_path=None)
        assert r.returncode == 0
        env_files = list(tmp_path.glob("claude_env*"))
        assert env_files == []

    def test_no_write_when_claude_env_file_empty_string(self, tmp_path):
        """CLAUDE_ENV_FILE='' must be treated as absent — no write, exits 0."""
        cwd = make_cwd(tmp_path / "proj5", config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook_with_env_file(cwd, env_file_path="")
        assert r.returncode == 0

    def test_symlink_skipped_with_warning(self, tmp_path):
        """CLAUDE_ENV_FILE pointing to a symlink must log WARNING and skip write."""
        real_file = tmp_path / "real_target"
        real_file.write_text("original")
        symlink = tmp_path / "claude_env_link"
        symlink.symlink_to(real_file)
        cwd = make_cwd(tmp_path / "proj6", config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook_with_env_file(cwd, env_file_path=symlink)
        assert r.returncode == 0
        assert "WARNING" in r.stderr
        assert real_file.read_text() == "original", "symlink target must not be modified"

    def test_debounce_non_integer_falls_back_to_3000(self, tmp_path):
        """Non-integer auto_test_debounce_ms must fall back to '3000' in env file."""
        env_file = tmp_path / "claude_env"
        cwd = make_cwd(tmp_path / "proj7", config={
            "auto_test_debounce_ms": "not-a-number",
        }, roadmap=SAMPLE_ROADMAP)
        run_hook_with_env_file(cwd, env_file_path=env_file)
        content = env_file.read_text()
        assert "ZIE_AUTO_TEST_DEBOUNCE_MS='3000'" in content

    def test_exit_0_when_env_file_not_writable(self, tmp_path):
        """Unwritable CLAUDE_ENV_FILE path must log to stderr and exit 0."""
        bad_path = tmp_path / "no_such_dir" / "claude_env"
        cwd = make_cwd(tmp_path / "proj8", config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook_with_env_file(cwd, env_file_path=bad_path)
        assert r.returncode == 0

    def test_returncode_0_when_zf_missing(self, tmp_path):
        """No zie-framework dir — hook exits 0 before env-file write; no write."""
        env_file = tmp_path / "claude_env"
        r = run_hook_with_env_file(tmp_path, env_file_path=env_file)
        assert r.returncode == 0
        assert not env_file.exists()
