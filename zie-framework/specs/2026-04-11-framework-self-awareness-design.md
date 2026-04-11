---
approved: true
approved_at: 2026-04-11
backlog: backlog/framework-self-awareness.md
---

# Framework Self-Awareness — Design Spec

**Problem:** Claude Code starts each session without deep knowledge of zie-framework's capabilities. It cannot proactively guide users to the right command, doesn't know the current project pipeline state, and silently degrades when the framework isn't initialized — missing the opportunity to help users get fully set up.

**Approach:** Two components — (A) `session-resume.py` extension: detect zie-framework state (uninitialized / stale / fresh), inject structured context block with command map + current state; (B) `/guide` command: user-invocable walkthrough of framework capabilities + recommended next actions.

**Relationship to intent-sdlc.py:** The session-start context block provides orientation at the beginning of each session (static, one-time). `intent-sdlc.py` provides reactive per-prompt hints during the session. They are complementary and non-overlapping.

**Out of Scope:** Adaptive command recommendations (covered by adaptive-learning spec). Per-prompt guidance (covered by intent-intelligence spec).

**Build Order (Dependency):**
1. Create `skills/using-zie-framework/SKILL.md` first (source of truth)
2. Then extend `hooks/session-resume.py` to read it
3. Then create `commands/guide.md`

**Components:**
- `skills/using-zie-framework/SKILL.md` — **CREATE** at `skills/using-zie-framework/SKILL.md` — source of truth for command map, workflow map, anti-patterns. Loaded as **plain text** by `session-resume.py` (via `Path.read_text()`), not registered as a callable skill and not invoked via `Skill()`. Hooks cannot call `Skill()` (no Claude tool access); therefore this file is consumed as static data. It is not listed in any hooks.json skill registry entry.
- `hooks/session-resume.py` — **MODIFY** — extend: parse using-zie-framework/SKILL.md key sections + detect init state + inject context block + proactive backlog nudge
- `hooks/hooks.json` — no change (session-resume.py already registered under SessionStart)
- `commands/guide.md` — **CREATE** — new `/guide` command

**Hardcoded Command List Fallback** (used when SKILL.md is unreadable):
```
[zie-framework] framework: commands — /backlog /spec /plan /implement /sprint /fix /chore /hotfix /guide /status /audit /retro /release /resync /init
[zie-framework] workflow: backlog→spec→plan→implement→release→retro
```
This fallback lists only commands that exist today. `/health`, `/rescue`, `/next` are **not** included — they are added to the fallback by their respective companion specs when those commands are created. This spec ships only the currently-existing command set.

**Staleness Detection:**
Reuse `is_mtime_fresh(max_mtime, written_at)` from `utils_roadmap.py`. Exact call:
```python
project_md_mtime = Path("zie-framework/PROJECT.md").stat().st_mtime
git_commit_mtime = float(subprocess.check_output(["git", "log", "-1", "--format=%ct"]).decode().strip())
# is_mtime_fresh(max_mtime, written_at) returns True when max_mtime <= written_at
# max_mtime=git_commit_mtime, written_at=project_md_mtime → True when git commit ≤ project_md → fresh
stale = not is_mtime_fresh(git_commit_mtime, project_md_mtime)
```
If git command fails → treat as fresh (skip warning, log to stderr).

**Data Flow:**

*A — session-resume.py extension (SessionStart):*
1. Check for `zie-framework/` dir in CWD:

   **Not found** → replace the current silent `sys.exit(0)` with:
   ```python
   print("[zie-framework] init: project not set up — run /init to initialize zie-framework")
   sys.exit(0)
   ```
   Note: the current implementation exits 0 silently when `zie-framework/` is absent (line 78 of `session-resume.py`). This spec **deliberately changes that path** to print the nudge before exiting. The corresponding unit test validates this new behavior.

   **Found, stale** → print warning:
   ```
   [zie-framework] knowledge: PROJECT.md outdated — run /resync to refresh
   ```
   Continue loading with stale data.

   **Found, fresh** → proceed normally.

2. Read `skills/using-zie-framework/SKILL.md` — extract command map + anti-patterns sections. On read failure: use hardcoded fallback list defined above.
3. Print structured context block to stdout. Commands marked `# conditional` are only included when `(cwd / "commands" / "<name>.md").exists()`:
   ```
   [zie-framework] framework: commands available — /backlog /spec /plan /implement /sprint /fix /chore /hotfix /guide /health /rescue /next /status /audit /retro /release /resync /init
   #                                                                                               ^^^^^^^ conditional  ^^^^^^^ conditional  ^^^^ conditional
   [zie-framework] workflow: backlog→spec→plan→implement→release→retro (use /sprint for full pipeline)
   [zie-framework] anti-patterns: never approve spec/plan directly; always run reviewer first; never skip pipeline on "ทำเลย"
   ```
   Guard: `(cwd / "commands" / "health.md").exists()` before including `/health`; same pattern for `/rescue` and `/next`. On a fresh checkout before companion specs ship, these three are omitted.

4. Backlog nudge: call `parse_roadmap_section(roadmap_path, "next")`. If ≥1 item in Next lane:
   ```
   [zie-framework] backlog: <N> item(s) pending — run /spec <item> to start designing
   ```

*B — using-zie-framework/SKILL.md content:*

**Command map** (existing + new commands from companion specs):

Existing commands:
- `/backlog` — capture a new idea
- `/spec` — design a backlog item
- `/plan` — plan implementation from approved spec
- `/implement` — TDD implementation (agent mode required)
- `/sprint` — full pipeline in one go
- `/fix` — debug and fix failing tests or broken features
- `/chore` — maintenance task, no spec needed
- `/hotfix` — emergency fix, ship fast
- `/status` — show current SDLC state
- `/audit` — project audit
- `/retro` — post-release retrospective
- `/release` — merge dev→main, version bump
- `/resync` — refresh project knowledge
- `/init` — bootstrap zie-framework in a new project

New commands (added by companion specs in this sprint):
- `/guide` — full framework walkthrough + recommended next actions (this spec)
- `/health` — framework health dashboard (observability spec)
- `/rescue` — pipeline state diagnosis + recovery path (error-recovery spec)
- `/next` — backlog prioritization + recommended next item (sprint-planning spec)

**Workflow map:** backlog → spec (reviewer) → plan (reviewer) → implement → release → retro

**Anti-patterns:**
- Never write `approved: true` directly — use `python3 hooks/approve.py`
- Never skip spec/plan steps on "ทำเลย" or similar
- Never run `/implement` without an approved plan
- Never approve without running the corresponding reviewer skill

*C — /guide command:*

**Acceptance criteria:**
- Given `zie-framework/` exists with ROADMAP.md and ≥1 item in Now lane: output includes that active feature name
- Given `zie-framework/` exists with ≥1 item in Next lane without approved spec: output recommends `/spec <item>`
- Given `zie-framework/` is absent: output contains the string `/init` and at least 2 sentences explaining what zie-framework is
- Given all backlog items have approved specs + plans: output recommends `/implement` or `/sprint`
- Given ROADMAP.md missing: output still shows command list; no crash

Implementation:
1. Read `zie-framework/` state: active feature via `parse_roadmap_section(roadmap_path, "now")`, pending items via `parse_roadmap_section(roadmap_path, "next")`, specs/, plans/
2. Determine pipeline position: for each Next-lane item, check `zie-framework/specs/` for a file matching slug `*<item-slug>-design.md`; read YAML frontmatter and check `approved: true`. Same check for `zie-framework/plans/`. Item state: no-spec | spec-unapproved | spec-approved-no-plan | plan-approved (ready to implement)
3. Print framework overview (commands + workflow)
4. Print recommended next 1-3 actions with exact commands to run
5. If `zie-framework/` absent: print setup guide + `/init` instructions

**Error Handling:**
- session-resume extension: Tier 1 outer guard (bare except → exit 0), never blocks session start
- using-zie-framework SKILL.md unreadable: print hardcoded fallback list (defined above)
- PROJECT.md unreadable: skip state awareness, still print command map
- `parse_roadmap_section()` fails: skip backlog nudge, continue
- /guide ROADMAP.md missing: skip pipeline position, show command list only
- /guide with no zie-framework/ dir: print setup guide + /init instructions (no error)

**Testing (`tests/unit/test_session_resume.py` **append** new test class + `tests/unit/test_guide.py` **create**):**
`@pytest.mark.error_path` is already registered (confirmed in `pytest.ini` line 4). New tests are **appended** to the existing file; no existing tests are removed or replaced.
- Unit: session-resume prints init prompt (containing "/init") when zie-framework/ absent
- Unit: session-resume prints resync warning (containing "/resync") when PROJECT.md stale per staleness check
- Unit: session-resume prints command list when fresh
- Unit: session-resume prints hardcoded fallback when SKILL.md unreadable
- Unit: session-resume prints backlog nudge when parse_roadmap_section("next") returns ≥1 item
- Unit: session-resume omits /health (and /rescue, /next) from command list when commands/health.md is absent; includes them when present
- Unit: session-resume exits 0 on malformed event (@pytest.mark.error_path)
- Unit: /guide output contains "/init" when zie-framework/ absent
- Unit: /guide output contains active feature name when ROADMAP Now lane has item
- Unit: /guide recommends /spec when Next lane item exists without approved spec
- Unit: /guide recommends /implement or /sprint when all Next lane items have approved spec + plan
- Unit: /guide shows command list when ROADMAP.md missing (no crash)
