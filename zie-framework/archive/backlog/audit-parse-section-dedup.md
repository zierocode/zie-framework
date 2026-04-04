# parse_section() in session-resume duplicates parse_roadmap_now logic

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`session-resume.py:41-52` defines an inline `parse_section()` function that
mirrors the core logic of `parse_roadmap_now()` in `utils.py`. Both extract
task lines from ROADMAP sections with nearly identical regex. They can diverge
silently.

## Motivation

`parse_roadmap_now()` or a generalized `parse_roadmap_section(section_name)`
in utils.py should replace the inline copy.
