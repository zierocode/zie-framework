"""Tests for same-context dedup cache in hooks/intent-sdlc.py.

The hook should skip re-injection when the emitted context is identical
to the last emission within the same session (keyed by session_id).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "intent-sdlc.py"


def run_hook(prompt: str, tmp_cwd: Path, session_id: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "ZIE_MEMORY_API_KEY": "", "CLAUDE_CWD": str(tmp_cwd)}
    event = {"session_id": session_id, "prompt": prompt}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path: Path, roadmap: str = "## Now\n\n## Next\n") -> Path:
    (tmp_path / "zie-framework").mkdir(parents=True, exist_ok=True)
    (tmp_path / "zie-framework" / "ROADMAP.md").write_text(roadmap)
    return tmp_path


SDLC_PROMPT = "implement this new feature in the codebase right now please"


class TestDedupCache:
    def test_first_call_emits_output(self, tmp_path):
        """First call with SDLC keyword must produce additionalContext output."""
        cwd = make_cwd(tmp_path)
        r = run_hook(SDLC_PROMPT, cwd, "test-dedup-first")
        assert r.returncode == 0
        assert r.stdout.strip() != "", "First call must emit additionalContext"

    def test_second_identical_call_deduped(self, tmp_path):
        """Second call with same session + same resulting context → no output."""
        cwd = make_cwd(tmp_path)
        session = "test-dedup-identical"

        r1 = run_hook(SDLC_PROMPT, cwd, session)
        assert r1.returncode == 0
        assert r1.stdout.strip() != "", "First call must emit"

        r2 = run_hook(SDLC_PROMPT, cwd, session)
        assert r2.returncode == 0
        assert r2.stdout.strip() == "", (
            "Second identical call in same session must be deduped (no output)"
        )

    def test_different_session_not_deduped(self, tmp_path):
        """Different session_id must not share the dedup cache."""
        cwd = make_cwd(tmp_path)

        r1 = run_hook(SDLC_PROMPT, cwd, "test-dedup-session-a")
        assert r1.stdout.strip() != "", "Session A first call must emit"

        r2 = run_hook(SDLC_PROMPT, cwd, "test-dedup-session-b")
        assert r2.stdout.strip() != "", (
            "Different session must not be deduped — fresh session gets full context"
        )

    def test_context_change_triggers_reemit(self, tmp_path):
        """When SDLC state changes (different active task), hook re-emits."""
        cwd = make_cwd(tmp_path, roadmap="## Now\n\n## Next\n")
        session = "test-dedup-change"

        # First call — idle state
        r1 = run_hook(SDLC_PROMPT, cwd, session)
        assert r1.stdout.strip() != "", "First call must emit"

        # Change ROADMAP state (add active Now task)
        (tmp_path / "zie-framework" / "ROADMAP.md").write_text(
            "## Now\n\n- [ ] my-feature\n\n## Next\n"
        )
        # Dedup cache is based on content; new active task → different context → re-emits
        r2 = run_hook(SDLC_PROMPT, cwd, session)
        assert r2.stdout.strip() != "", (
            "Changed ROADMAP state must trigger re-emission despite same session"
        )
