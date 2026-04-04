---
slug: audit-playwright-version-check
status: approved
approved: true
date: 2026-04-01
spec: zie-framework/specs/2026-04-01-audit-playwright-version-check-design.md
---

# Plan: audit-playwright-version-check

## Overview

Two focused changes to `hooks/session-resume.py` plus new unit tests:

1. **Diagnostic log on subprocess error** — print `[session-resume] playwright version check failed: <err>` to stderr when `subprocess.run` raises.
2. **Config-driven required version** — read `required_playwright_version` from `zie-framework/.config` at runtime; fall back to `REQUIRED_PW_VERSION = "1.51.0"`.
3. **Test coverage** — extend `tests/unit/test_session_resume.py` to cover all three check paths and the config-override path.

---

## Files Touched

| File | Change |
|------|--------|
| `hooks/session-resume.py` | Patch `_check_playwright_version` (two changes) |
| `tests/unit/test_session_resume.py` | Add four new test cases |

---

## Task 1 — Diagnostic log on subprocess error

### RED step

Add to `tests/unit/test_session_resume.py` inside `TestCheckPlaywrightVersion`:

```python
def test_subprocess_error_logs_diagnostic(self, capsys):
    with patch("subprocess.run", side_effect=Exception("pw not found")):
        session_resume._check_playwright_version({"playwright_enabled": True})
    captured = capsys.readouterr()
    assert "playwright version check failed" in captured.err
    assert "pw not found" in captured.err
```

Run: `make test-unit` — expect RED.

### GREEN step

Patch `_check_playwright_version` in `hooks/session-resume.py`:

```python
    except Exception as e:
        print(
            f"[session-resume] playwright version check failed: {e}",
            file=sys.stderr,
        )
        installed = "unknown"
```

Run: `make test-unit` — expect GREEN.

### REFACTOR step

Confirm existing `test_subprocess_error_sets_unknown` still passes.

---

## Task 2 — Config-driven required version

### RED step

Add two failing tests:

```python
def test_config_version_overrides_fallback(self, capsys):
    """When config supplies required_playwright_version, use it."""
    mock_result = MagicMock()
    mock_result.stdout = "Version 1.99.0\n"
    with patch("subprocess.run", return_value=mock_result):
        session_resume._check_playwright_version(
            {"playwright_enabled": True, "required_playwright_version": "1.99.0"}
        )
    captured = capsys.readouterr()
    assert captured.err == ""

def test_fallback_version_used_when_key_absent(self, capsys):
    """When config lacks required_playwright_version, hardcoded fallback applies."""
    mock_result = MagicMock()
    mock_result.stdout = f"Version {session_resume.REQUIRED_PW_VERSION}\n"
    with patch("subprocess.run", return_value=mock_result):
        session_resume._check_playwright_version({"playwright_enabled": True})
    captured = capsys.readouterr()
    assert captured.err == ""
```

Run: `make test-unit` — expect RED on `test_config_version_overrides_fallback`.

### GREEN step

Replace `_check_playwright_version` in `hooks/session-resume.py`:

```python
def _check_playwright_version(config: dict) -> None:
    if not config.get("playwright_enabled"):
        return

    required = config.get("required_playwright_version", REQUIRED_PW_VERSION)

    try:
        result = subprocess.run(
            ["playwright", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        installed = result.stdout.strip().split()[-1]
    except Exception as e:
        print(
            f"[session-resume] playwright version check failed: {e}",
            file=sys.stderr,
        )
        installed = "unknown"

    if installed != required:
        print(
            f"[session-resume] Playwright version mismatch: "
            f"installed={installed}, required={required}",
            file=sys.stderr,
        )
```

Run: `make test-unit` — expect GREEN on all six playwright tests.

---

## Task 3 — Full test-unit verification

```bash
make test-unit
```

Expected: all tests pass, coverage includes both new branches.

---

## Test Strategy

All new tests are **unit tests** using `unittest.mock.patch` to stub `subprocess.run`.

| Test | Covers | AC |
|------|--------|----|
| `test_subprocess_error_logs_diagnostic` | stderr log on subprocess error | AC1 |
| `test_config_version_overrides_fallback` | config key overrides hardcoded fallback | AC2, AC4 |
| `test_fallback_version_used_when_key_absent` | hardcoded fallback when key absent | AC2, AC5 |
| *(existing)* `test_version_mismatch_emits_warning` | mismatch warning preserved | AC3 |
| *(existing)* `test_subprocess_error_sets_unknown` | unknown triggers mismatch warning | AC1 (partial) |

---

## Rollout

1. Implement Task 1 (RED → GREEN → REFACTOR).
2. Implement Task 2 (RED → GREEN → REFACTOR).
3. Run `make test-unit` — full green gate.
4. Run `make test-ci` — confirm no regressions.
5. No `.config` migration needed — new key is optional.
