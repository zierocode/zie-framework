# Backlog: Reviewer Skills → Custom Agents with Persistent Memory

**Problem:**
spec-reviewer, plan-reviewer, and impl-reviewer run as inline skills — they
pollute main conversation context, use full Sonnet model, have no memory of
past reviews, and can't be run in isolation. Quality doesn't improve over time.

**Motivation:**
Claude Code custom agents support `memory: project` (cross-session learning),
`model: haiku` (3x faster, 5x cheaper), `permissionMode: plan` (read-only
safe), and isolated context. Converting reviewers to agents means: (1) past
review patterns accumulate, (2) isolated execution doesn't pollute the main
conversation, (3) haiku is fast enough for structured review tasks.

**Rough scope:**
- Create `agents/spec-reviewer.md` — tools: Read/Grep/Glob, model: haiku,
  permissionMode: plan, memory: project, user-invocable: false
- Create `agents/plan-reviewer.md` — same profile
- Create `agents/impl-reviewer.md` — tools: Read/Grep/Glob/Bash(make test*),
  model: haiku, memory: project
- Update /zie-spec, /zie-plan, /zie-implement commands to `@agent-spec-reviewer`
  etc. instead of `Skill(zie-framework:spec-reviewer)`
- Agents use `skills:` field to preload relevant context at startup
- Tests: agent files parse correctly, memory dirs created
