"""Unit tests for _is_safe_for_confirmation_wrapper in safety-check.py."""

import importlib.util
import sys
import types
from pathlib import Path

HOOKS_DIR = Path(__file__).parent.parent.parent / "hooks"


# Stub side-effectful modules so safety-check.py can be imported without running hooks
def _stub_module(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules.setdefault(name, m)


_stub_module("utils_safety", COMPILED_BLOCKS=[], COMPILED_WARNS=[], normalize_command=lambda x: x)
_stub_module("utils_event", get_cwd=lambda: Path("."), read_event=lambda: {})
_stub_module("utils_io", project_tmp_path=lambda *a: Path("/tmp/stub"))
_stub_module("utils_config", load_config=lambda *a: {})
_stub_module("safety_check_agent", evaluate=lambda *a, **kw: 0)

# safety-check.py has a hyphen — must use importlib
_spec = importlib.util.spec_from_file_location("safety_check", HOOKS_DIR / "safety-check.py")
_mod = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(_mod)
except SystemExit:
    pass  # module-level sys.exit(0) when event is missing — expected

_is_safe_for_confirmation_wrapper = _mod._is_safe_for_confirmation_wrapper


class TestIsSafeForConfirmationWrapper:
    """Guard must reject redirect/pipe metacharacters that enable injection in confirm-wrap."""

    def test_stdout_redirect_rejected(self):
        """> (stdout redirect) must be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo > /etc/passwd") is False

    def test_stdin_redirect_rejected(self):
        """< (stdin redirect) must be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo < /dev/urandom") is False

    def test_pipe_rejected(self):
        """| (pipe) must be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo | tee /etc/passwd") is False

    def test_newline_rejected(self):
        """Literal newline must be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo\necho pwned") is False

    def test_safe_command_passes(self):
        """Plain safe command must still pass."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo") is True

    def test_safe_command_with_path_passes(self):
        """Path-only rm commands must still pass."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./build") is True

    def test_semicolon_still_rejected(self):
        """; (semicolon) must still be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo; echo pwned") is False

    def test_double_ampersand_still_rejected(self):
        """&& must still be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo && echo pwned") is False

    def test_double_pipe_still_rejected(self):
        """|| must still be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./foo || echo pwned") is False

    def test_backtick_still_rejected(self):
        """` (backtick) must still be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./`echo foo`") is False

    def test_subshell_still_rejected(self):
        """$() must still be rejected."""
        assert _is_safe_for_confirmation_wrapper("rm -rf ./$(echo foo)") is False
