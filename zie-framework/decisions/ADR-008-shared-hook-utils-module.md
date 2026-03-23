# ADR-008: Shared Hook Utility Module (hooks/utils.py)

Date: 2026-03-23
Status: Accepted

## Context

Multiple hooks duplicated the same ROADMAP parsing logic (40+ lines) and
each generated `/tmp` filenames independently, causing cross-project
collisions when two projects using zie-framework ran simultaneously in the
same shell session.

## Decision

Introduce `hooks/utils.py` as a shared stdlib-only Python module. Hooks
import it via `sys.path.insert(0, os.path.dirname(__file__))` — no pip
dependency, no package install step. The module exposes two helpers:
`parse_roadmap_now(roadmap_file)` and `project_tmp_path(name, project)`.

## Consequences

__Positive:__ Eliminates ~40 lines of duplicated inline ROADMAP parsing;
`project_tmp_path` scopes all `/tmp` files to `zie-{project}-{name}`,
preventing cross-project state bleed.

__Negative:__ `sys.path.insert` is a side-effect on import — hooks must be
careful not to pollute path for callers that import them in tests.

__Neutral:__ All hooks that read ROADMAP or write `/tmp` now have a shared
dependency; changes to `utils.py` affect multiple hooks simultaneously.
