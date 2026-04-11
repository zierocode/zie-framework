# Framework Self-Awareness

**Status:** spec-ready
**Priority:** high
**Created:** 2026-04-11

Claude Code starts each session without deep knowledge of zie-framework's capabilities, cannot proactively guide users to the right command, and silently degrades when the framework isn't initialized.

Build a `using-zie-framework` skill (loaded at session start) that gives Claude a complete command map + current project state, plus a `/guide` command for user-invocable walkthroughs. Detect uninitialized projects and actively prompt to run `/init`.

**Spec:** `zie-framework/specs/2026-04-11-framework-self-awareness-design.md`
