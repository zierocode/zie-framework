"""Tests for hooks/intent-detect.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_hook(event, tmp_cwd=None, env_overrides=None):
    hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run([sys.executable, hook], input=json.dumps(event),
                          capture_output=True, text=True, env=env)


def make_cwd_with_zf(tmp_path):
    (tmp_path / "zie-framework").mkdir(parents=True)
    return tmp_path


class TestIntentDetectHappyPath:
    def _parse_command(self, r):
        assert r.stdout.strip() != ""
        return json.loads(r.stdout)["additionalContext"]

    def test_fix_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "there is a bug in the auth module"}, tmp_cwd=cwd)
        assert "/zie-fix" in self._parse_command(r)

    def test_implement_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "start coding this task now"}, tmp_cwd=cwd)
        assert "/zie-implement" in self._parse_command(r)

    def test_release_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "ready to deploy and release now"}, tmp_cwd=cwd)
        assert "/zie-release" in self._parse_command(r)

    def test_plan_intent_thai(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "อยากวางแผน feature ใหม่"}, tmp_cwd=cwd)
        assert "/zie-plan" in self._parse_command(r)

    def test_backlog_intent_thai(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "อยากเพิ่ม feature ใหม่"}, tmp_cwd=cwd)
        assert "/zie-backlog" in self._parse_command(r)


class TestIntentDetectGuardrails:
    def test_no_output_when_no_zf_dir(self, tmp_path):
        r = run_hook({"prompt": "fix this bug"}, tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""

    def test_no_output_for_zie_command_prompt(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "/zie-implement the feature"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_output_for_empty_prompt(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": ""}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_output_for_short_prompt(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "ok"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_output_for_invalid_json(self, tmp_path):
        hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run([sys.executable, hook], input="not json",
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_init_suppressed_when_config_exists(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        (cwd / "zie-framework" / ".config").write_text('{}')
        r = run_hook({"prompt": "init the project bootstrap setup"}, tmp_cwd=cwd)
        assert "/zie-init" not in r.stdout


class TestIntentDetectCompiledPatterns:
    def test_compiled_patterns_exist_at_module_level(self, tmp_path):
        """Verify COMPILED_PATTERNS is built at import time, not in the scoring loop."""
        import importlib.util
        import io
        # Create zie-framework dir so the hook passes the cwd guard and reaches
        # COMPILED_PATTERNS. Use a prompt that matches nothing so it exits after
        # COMPILED_PATTERNS is defined (at the "if not scores" guard).
        (tmp_path / "zie-framework").mkdir()
        hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
        spec = importlib.util.spec_from_file_location("intent_detect", hook)
        mod = importlib.util.module_from_spec(spec)
        original_stdin = sys.stdin
        original_env = os.environ.copy()
        try:
            sys.stdin = io.StringIO('{"prompt": "hello world this is a neutral message"}')
            os.environ["CLAUDE_CWD"] = str(tmp_path)
            try:
                spec.loader.exec_module(mod)
            except SystemExit:
                pass
        finally:
            sys.stdin = original_stdin
            os.environ.clear()
            os.environ.update(original_env)
        assert hasattr(mod, "COMPILED_PATTERNS")
        # All values should be lists of compiled patterns
        import re as re_mod
        for cat, pats in mod.COMPILED_PATTERNS.items():
            for p in pats:
                assert isinstance(p, re_mod.Pattern), f"{cat}: {p!r} is not a compiled pattern"


class TestIntentDetectSkipGuards:
    def test_frontmatter_prompt_produces_empty_stdout(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "---\ntitle: My Note\n---\nsome content"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_long_message_produces_empty_stdout(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "x" * 501}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_500_char_message_not_suppressed(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        # 500 chars total with clear bug/fix keywords — should NOT be suppressed
        r = run_hook({"prompt": "fix the bug " + "x" * 488}, tmp_cwd=cwd)
        assert r.stdout.strip() != ""


class TestIntentDetectReDoSGuard:
    def test_message_at_limit_is_not_rejected(self, tmp_path):
        """Exactly MAX_MESSAGE_LEN chars — should NOT be suppressed by length guard."""
        cwd = make_cwd_with_zf(tmp_path)
        msg = "fix " + "x" * 996  # 1000 chars total
        r = run_hook({"prompt": msg}, tmp_cwd=cwd)
        assert r.returncode == 0

    def test_message_over_limit_produces_no_output(self, tmp_path):
        """1001 chars — MAX_MESSAGE_LEN guard must fire, producing no output."""
        cwd = make_cwd_with_zf(tmp_path)
        msg = "fix " + "x" * 997  # 1001 chars total
        r = run_hook({"prompt": msg}, tmp_cwd=cwd)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_max_message_len_constant_is_1000(self):
        """MAX_MESSAGE_LEN must be defined as 1000 in the hook module."""
        import importlib.util, io
        hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
        spec = importlib.util.spec_from_file_location("intent_detect_redos", hook)
        mod = importlib.util.module_from_spec(spec)
        original_stdin = sys.stdin
        original_env = os.environ.copy()
        try:
            sys.stdin = io.StringIO('{"prompt": "hi"}')
            os.environ["CLAUDE_CWD"] = "/tmp"
            try:
                spec.loader.exec_module(mod)
            except SystemExit:
                pass
        finally:
            sys.stdin = original_stdin
            os.environ.clear()
            os.environ.update(original_env)
        assert hasattr(mod, "MAX_MESSAGE_LEN"), "MAX_MESSAGE_LEN constant not found"
        assert mod.MAX_MESSAGE_LEN == 1000


class TestIntentDetectModuleLevelConstants:
    def test_patterns_defined_before_any_conditional(self):
        """PATTERNS must appear before any if/try block in the source file."""
        import ast
        hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
        src = open(hook).read()
        tree = ast.parse(src)

        patterns_line = None
        first_conditional_line = None

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "PATTERNS":
                        patterns_line = node.lineno
            if isinstance(node, (ast.If, ast.Try)) and first_conditional_line is None:
                first_conditional_line = node.lineno

        assert patterns_line is not None, "PATTERNS assignment not found"
        assert first_conditional_line is not None, "No conditional found (unexpected)"
        assert patterns_line < first_conditional_line, (
            f"PATTERNS (line {patterns_line}) must be defined before first "
            f"conditional (line {first_conditional_line})"
        )
