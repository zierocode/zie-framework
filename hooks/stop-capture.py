#!/usr/bin/env python3
"""Stop hook — write .zie/handoff.md from implicit design conversations.

Synchronous (no background: true) — handoff.md must be flushed before session
closes so /sprint can read it in the next session.

Secondary write path: only fires when brainstorm skill did NOT already run.
Brainstorm skill sets the 'brainstorm-active' flag; this hook skips if set.
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_cache import get_cache_manager
from utils_error import log_error
from utils_event import get_cwd, read_event
from utils_io import atomic_write

try:
    event = read_event()
except Exception as e:
    log_error("stop-capture", "read_event", e)
    sys.exit(0)

try:
    session_id = event.get("session_id", "") or "default"
    cwd = get_cwd()
    project = cwd.name
    cache = get_cache_manager(cwd)

    # Skip if brainstorm skill already ran (it's the primary writer)
    if cache.has_flag("brainstorm-active", session_id):
        sys.exit(0)

    # Skip if no design conversation detected this session
    if not cache.has_flag("design-mode", session_id):
        sys.exit(0)

    # Create .zie/ dir if absent
    zie_dir = cwd / ".zie"
    try:
        zie_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[zf] stop-capture: cannot create .zie/: {e}", file=sys.stderr)
        sys.exit(0)

    # Write handoff.md
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    handoff_content = f"""---
captured_at: {now}
feature: design-session
source: design-tracker
---

## Goals
- (captured from design conversation — review and refine before running /sprint)

## Key Decisions
- (key decisions made during this session)

## Constraints
- (constraints mentioned during discussion)

## Open Questions
- (unresolved questions to address)

## Context Refs
- (relevant file paths or commands mentioned)

## Next Step
/sprint <feature-name>
"""
    handoff_path = zie_dir / "handoff.md"
    try:
        atomic_write(handoff_path, handoff_content)
    except Exception as e:
        print(f"[zf] stop-capture: handoff write failed: {e}", file=sys.stderr)
        sys.exit(0)

    # Cleanup design-mode flag
    try:
        cache.delete("design-mode", session_id)
    except Exception as _e:
        print(f"[zf] stop-capture: flag cleanup failed: {_e}", file=sys.stderr)

except Exception as e:
    log_error("stop-capture", "main", e)
    sys.exit(0)
