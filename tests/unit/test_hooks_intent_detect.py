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
    def test_fix_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "there is a bug in the auth module"}, tmp_cwd=cwd)
        assert "/zie-fix" in r.stdout

    def test_build_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "start coding this task now"}, tmp_cwd=cwd)
        assert "/zie-build" in r.stdout

    def test_ship_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "ready to ship and deploy now"}, tmp_cwd=cwd)
        assert "/zie-ship" in r.stdout

    def test_plan_intent_thai(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "อยากวางแผน feature ใหม่"}, tmp_cwd=cwd)
        assert "/zie-plan" in r.stdout

    def test_idea_intent_thai(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "อยากเพิ่ม feature ใหม่"}, tmp_cwd=cwd)
        assert "/zie-idea" in r.stdout


class TestIntentDetectGuardrails:
    def test_no_output_when_no_zf_dir(self, tmp_path):
        r = run_hook({"prompt": "fix this bug"}, tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""

    def test_no_output_for_zie_command_prompt(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "/zie-build the feature"}, tmp_cwd=cwd)
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
