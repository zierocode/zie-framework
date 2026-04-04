# subagent-context: Skip Plan File Read for Explore Agents

## Problem

`subagent-context.py:59` reads the full most-recent plan file on every SubagentStart event for Explore/Plan agents. It then scans for the first `- [ ]` task line. Explore agents scanning the codebase for architecture patterns don't need the current incomplete task from an implementation plan — only Plan agents benefit from this context.

## Motivation

Unnecessary full file read + line scan on every Explore subagent spawn. During `/zie-implement`, which may spawn multiple Explore agents for codebase research, this fires repeatedly with data that Explore agents don't act on.

## Rough Scope

- Gate the plan file read behind a check for Plan-type agents (not Explore)
- Parse the agent type from the SubagentStart event input
- Explore agents only need the feature slug and ADR count from the context injection
