---
tags: [feature]
---

# Cache load_config() Reads in Hot-Path Hooks

## Problem

`load_config()` reads and JSON-parses `zie-framework/.config` on every hook invocation with no in-process caching. Since each hook is a separate Python process, the file is read + parsed + validated on every PreToolUse event (safety-check fires on every Write/Edit/Bash). Similarly, `shutil.which('claude')` scans PATH directories on every Bash PreToolUse.

## Motivation

These are the hottest path in the plugin. Each PreToolUse event pays the cost of config parsing and PATH scanning unnecessarily.

## Rough Scope

- Add module-level cache for `load_config()` with mtime-based invalidation (same pattern as roadmap cache)
- Cache `shutil.which('claude')` result at module level (PATH doesn't change within a hook process)
- Add cache invalidation test