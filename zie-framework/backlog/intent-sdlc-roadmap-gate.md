# intent-sdlc: Skip ROADMAP Read for Non-Now-Dependent Intents

## Problem

After intent detection passes in `intent-sdlc.py`, `read_roadmap_cached()` fires unconditionally — even for intents like `backlog`, `spec`, `retro`, and `audit` that don't use Now-lane content. Only `plan`, `implement`, and `status` intents actually consume the Now lane to inject a gate message. The ROADMAP cache TTL is 30 seconds so within the window reads are cheap, but `parse_roadmap_section_content()` still runs on every match.

## Motivation

This fires on literally every user prompt that matches an SDLC keyword. Over a 100-turn session, non-Now intents trigger unnecessary ROADMAP string scans. Gating the read behind `if detected_intent in ("plan", "implement", "status")` eliminates the work for all other intent types.

## Rough Scope

- Identify which intents in `intent-sdlc.py` actually use Now-lane content
- Gate `read_roadmap_cached()` call behind those intents only
- Update tests for non-Now intent handling
