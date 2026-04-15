---
tags: [chore]
---

# Compress Status Command

## Problem

`/status` is 865 words with verbose test health detection (10 lines) and velocity computation (14 lines of bash + parsing). The model already knows pytest cache patterns and git log syntax.

Estimated reduction: ~355 words → ~510 words remaining.

Note: This is separate from `status-roadmap-content` (adding ROADMAP items to output). This item is about compressing existing verbose instructions.

## Motivation

/status fires frequently for orientation. Leaner instructions mean faster orientation with less token waste.

## Rough Scope

**In:**
- Compress test health detection to 1-2 lines
- Compress velocity computation to 1-2 lines
- Compress pipeline stage indicator to 1-2 lines

**Out:**
- Changing status output format
- Changing what status reports (that's status-roadmap-content)