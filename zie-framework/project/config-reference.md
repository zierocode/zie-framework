# Hook Configuration Reference

Optional keys in `zie-framework/.config` (JSON):

| Key | Default | Values | Description |
| --- | --- | --- | --- |
| `safety_check_mode` | `"regex"` | `"regex"`, `"agent"`, `"both"` | Controls `safety_check_agent.py`. `"regex"` — fast pattern matching only, no subprocess spawned. `"agent"` — spawns a Claude subagent on every Bash call to evaluate safety. `"both"` — runs regex first, then agent. Use `"regex"` unless you need AI-level judgment on commands. |
| `subprocess_timeout_s` | `5` | `int` | Timeout (s) for `git` subprocess calls in `failure-context.py` and `stop-handler.py`. |
| `safety_agent_timeout_s` | `30` | `int` | Timeout (s) for the Claude subagent subprocess in `safety_check_agent.py`. |
| `auto_test_max_wait_s` | `15` | `int` | Wall-clock kill limit (s) for `auto-test.py`. Set to `0` to disable (falls back to `auto_test_timeout_ms`). |
| `auto_test_timeout_ms` | `30000` | `int` | Fallback subprocess timeout (ms) for `auto-test.py` when `auto_test_max_wait_s` is `0`. |
| `compact_hint_threshold` | `0.8` | `float` | Usage fraction (0.0–1.0) at which the Stop hook prints the `/compact` hint. Set to `1.0` to disable. |
