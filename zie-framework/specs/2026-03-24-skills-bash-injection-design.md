---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-bash-injection.md
---

# Skills !`cmd` Bash Injection for Live Context — Design Spec

**Problem:** Skills that need current project state (git log, ROADMAP contents,
knowledge hash) must wait 3-5 extra tool-call turns while Claude gathers that
context via Bash, delaying every invocation of zie-implement, zie-status, and
zie-retro.

**Approach:** Use the `!`command`` bash-injection syntax supported in Claude Code
skill files — shell commands embedded in a SKILL.md are executed before the skill
content is delivered to Claude, with stdout replacing the placeholder inline.
Each of the three affected skills gains a small set of injections that capture
the exact live data the skill needs (git log, git status, ROADMAP head, knowledge
hash) so Claude receives a fully-rendered context bundle with zero additional
tool calls. All injections must complete in under 500 ms, use no network calls,
and degrade gracefully (empty output or a "unavailable" placeholder) when the
underlying command fails or the binary is missing.

**Components:**

- Modify: `skills/tdd-loop/SKILL.md` — no changes (tdd-loop does not use live
  context; listed here only to confirm it is excluded)
- Modify: `commands/zie-implement.md` — the pre-flight Bash calls in steps 5
  and the end-of-feature `git status --short` can be removed once bash injection
  covers them; zie-implement's SKILL.md invocation passes through the injected
  context automatically
- Modify: `skills/` — the three skills that own the live-context gathering are
  NOT skills themselves; the injections live in the command files and any skill
  that directly embeds the context. Concretely:
  - Modify: `commands/zie-implement.md` — add bash injections at the top of the
    "ตรวจสอบก่อนเริ่ม" section:
    - `` !`git log -5 --oneline` `` → recent commit history
    - `` !`git status --short` `` → uncommitted file list
    - `` !`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now 2>/dev/null || echo "knowledge-hash: unavailable"` `` → live knowledge hash
  - Modify: `commands/zie-status.md` — add bash injections at the top of the
    Steps section:
    - `` !`cat zie-framework/ROADMAP.md | head -30` `` → ROADMAP snapshot
    - `` !`python3 hooks/knowledge-hash.py 2>/dev/null || echo "knowledge-hash: unavailable"` `` → live knowledge hash for drift check
  - Modify: `commands/zie-retro.md` — add bash injections at the top of the
    "ตรวจสอบก่อนเริ่ม" section:
    - `` !`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline` `` → commits since last tag
    - `` !`git log -20 --oneline` `` → recent activity window
- Create: `tests/unit/test_skills_bash_injection.py` — pytest assertions
  verifying that each modified command file contains the expected injection
  patterns and that `${CLAUDE_SKILL_DIR}` variable form is used for
  script-relative paths

**Data Flow:**

1. User invokes a command (e.g. `/zie-implement`, `/zie-status`, `/zie-retro`).
2. Claude Code reads the command's Markdown file before rendering it to Claude.
3. For each `` !`cmd` `` placeholder encountered, Claude Code executes the shell
   command with the project's CWD as the working directory.
4. stdout of the command replaces the `` !`cmd` `` token inline in the rendered
   Markdown. If the command exits non-zero or produces no output, an empty string
   or the fallback string after `||` is substituted (see per-command fallbacks
   in Components above).
5. Claude receives the fully-rendered Markdown — it sees the actual git log,
   actual ROADMAP head, and actual knowledge hash as literal text, not as tool
   calls it must make.
6. Claude proceeds directly to reasoning/action with no additional Bash turns
   needed for the pre-flight context already injected.
7. Commands that previously issued explicit `git status --short` Bash blocks as
   part of their step instructions (zie-implement steps 5 and end-of-feature
   commit review) should be updated to reference the already-injected value
   instead of re-running Bash — reducing redundant subprocess calls.

**Edge Cases:**

- **Command not found / binary missing:** Each injection uses `|| echo
  "unavailable"` or `2>/dev/null` so a missing `git`, missing
  `knowledge-hash.py`, or a repo with no tags never produces an error that
  blocks skill delivery. Claude sees an "unavailable" string and adjusts
  its reasoning accordingly.
- **No git tags yet (zie-retro injection):** `git describe --tags --abbrev=0`
  fails on repos with no tags; the `|| git rev-list --max-parents=0 HEAD`
  fallback returns the initial commit SHA, producing a valid `git log` range
  covering the entire history.
- **CWD mismatch:** Injections that reference relative paths (`zie-framework/
  ROADMAP.md`, `hooks/knowledge-hash.py`) assume CWD is the project root.
  Claude Code always sets CWD to the project root before command execution —
  this is consistent with how hooks and commands operate today. Injections using
  `${CLAUDE_SKILL_DIR}` resolve relative to the skill/command file regardless
  of CWD, providing an explicit safe path for script references.
- **ROADMAP.md missing:** `cat zie-framework/ROADMAP.md | head -30` exits
  non-zero if the file does not exist; the empty output causes Claude to see a
  blank ROADMAP block, which triggers the existing "Not initialized — run
  /zie-init" guard in zie-status step 1.
- **Slow git operations on large repos:** `git log -5 --oneline` and `git status
  --short` are bounded operations (5 lines, local index only) and complete well
  under 500 ms on any repo size. `git log $(git describe...)..HEAD --oneline`
  for zie-retro could be longer on a repo with many commits since last tag, but
  has no network calls and no object traversal limits — acceptable for a retro
  context.
- **knowledge-hash.py --now flag:** The `--now` flag is used in zie-implement's
  injection to compute a live hash. The flag must already be supported by
  `hooks/knowledge-hash.py`. If it is not, the `2>/dev/null || echo
  "knowledge-hash: unavailable"` fallback keeps the injection safe; the
  implementation plan must confirm flag support before relying on it.
- **Injection output too long:** ROADMAP `head -30` caps output at 30 lines.
  `git log -5` caps at 5 commits. `git status --short` output size is
  proportional to dirty files; in normal operation this is small. No injection
  is unbounded.
- **Interaction with `context: fork` reviewer skills:** Reviewer skills
  (spec-reviewer, plan-reviewer, impl-reviewer) run in forked subagents per
  the skills-fork-context spec. Those skills do not use bash injection — they
  load context via Phase 1 Read/Grep/Glob tool calls. This spec does not touch
  reviewer skills.

**Out of Scope:**

- Adding bash injection to any skill file (`skills/*/SKILL.md`) — injections
  are added to command files (`commands/zie-*.md`) only, where live state is
  gathered at command entry.
- Adding bash injection to hooks — hooks already run as Python subprocesses
  with full shell access.
- Network-calling injections of any kind (no `curl`, no MCP calls, no
  `pip install`).
- Changing the output format or display of any command — injections provide
  raw data that commands already know how to use; no command logic changes
  except removing the now-redundant explicit Bash blocks.
- Adding injection to commands that do not currently gather live state at
  startup: `zie-backlog`, `zie-spec`, `zie-plan`, `zie-release`, `zie-init`,
  `zie-resync`, `zie-audit`, `zie-fix`.
- Caching or memoising injection output across multiple command invocations.
- Modifying `hooks/knowledge-hash.py` itself — if the `--now` flag is missing,
  that is a separate fix tracked in its own backlog item.
