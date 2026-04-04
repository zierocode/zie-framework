# Design: safety-check-compiled-blocks

**Date:** 2026-04-04
**Slug:** safety-check-compiled-blocks
**Status:** Approved

## Problem

`safety_check_agent.py:44` calls `re.search(pattern, cmd)` inside `_regex_evaluate`, iterating over `_AGENT_BLOCKS` which is built from raw string tuples. `utils_safety` already exports `COMPILED_BLOCKS` — patterns pre-compiled at import time — specifically to avoid per-call recompilation overhead. The fallback regex path bypasses this optimisation entirely.

## Solution

Add `COMPILED_BLOCKS` to the import from `utils_safety`. Build `_COMPILED_AGENT_BLOCKS` at module level (mirroring how `COMPILED_BLOCKS` is built), then use `p.search(cmd)` in `_regex_evaluate`.

## Acceptance Criteria

1. `safety_check_agent.py` imports `COMPILED_BLOCKS` from `utils_safety`.
2. `_AGENT_BLOCKS` (string tuples) is replaced or supplemented by `_COMPILED_AGENT_BLOCKS` (compiled pattern + message tuples) at module level.
3. `_regex_evaluate` loops over `_COMPILED_AGENT_BLOCKS` using `p.search(cmd)` — no bare `re.search` call with a string pattern.
4. `import re` may be removed if no longer used elsewhere in the file.
5. All existing tests in `test_safety_check_agent_injection.py` pass without modification.
6. No behavioural change — blocked commands still block, allowed commands still pass.

## Out of Scope

- Changes to `utils_safety.py`.
- Changes to other hooks that already use `COMPILED_BLOCKS`.
