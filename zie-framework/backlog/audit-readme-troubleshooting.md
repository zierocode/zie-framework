# README missing troubleshooting section and links to SECURITY/CHANGELOG

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

README.md references SECURITY.md and CHANGELOG.md in descriptions but provides
no direct links. There is no troubleshooting section — common issues like
"hook not firing", "zie-memory not connecting", or "tests not auto-running" are
undocumented. New users have no self-service path when things go wrong.

## Motivation

A troubleshooting FAQ reduces friction during initial setup. Linking to
SECURITY.md and CHANGELOG from README improves discoverability for contributors
and security researchers.
