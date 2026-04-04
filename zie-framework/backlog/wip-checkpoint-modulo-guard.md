# wip-checkpoint: Move Edit Counter Write to After Modulo Gate

## Problem

`wip-checkpoint.py:47` increments and atomically writes the persistent edit counter (via `safe_write_persistent` — NamedTemporaryFile + os.replace + os.chmod) on every Edit/Write event, including the 4 out of 5 that immediately exit after the modulo check at line 51. The I/O happens before the gate.

## Motivation

4 unnecessary atomic file writes + chmod syscalls for every 5 edits. Over a session with hundreds of edits, this is constant avoidable I/O. The fix is trivial: read the counter, check modulo, only write if the checkpoint should fire.

## Rough Scope

- Restructure `wip-checkpoint.py` to: read counter → increment → check modulo → write only if `count % 5 == 0`
- Update tests for the checkpoint firing logic
