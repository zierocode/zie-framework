#!/usr/bin/env python3
"""UserPromptSubmit hook — detect SDLC intent and suggest the right /zie-* command."""
import sys
import json
import os
import re
from pathlib import Path

try:
    event = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

message = (event.get("prompt") or "").lower().strip()

if not message or len(message) < 3:
    sys.exit(0)

# Only run if zie-framework is initialized in cwd
cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
if not (cwd / "zie-framework").exists():
    sys.exit(0)

# Suppress if user is explicitly running a /zie-* command already
if message.startswith("/zie-"):
    sys.exit(0)

# Pattern definitions — (regex patterns, signal weight)
PATTERNS = {
    "init": [
        r"\binit\b", r"เริ่มต้น.*project", r"ตั้งค่า.*project",
        r"setup.*project", r"bootstrap",
    ],
    "idea": [
        r"อยากทำ", r"อยากได้", r"อยากเพิ่ม", r"อยากสร้าง",
        r"\bidea\b", r"\bfeature\b", r"new feature", r"เพิ่ม.*feature",
        r"สร้าง.*ใหม่", r"want to (build|add|create|make)",
        r"ต้องการ", r"would like to",
    ],
    "plan": [
        r"\bplan\b", r"วางแผน", r"อยากวางแผน", r"เลือก.*backlog",
        r"หยิบ.*backlog", r"plan.*feature", r"ready.*to.*plan",
        r"zie.?plan",
    ],
    "build": [
        r"implement", r"ทำ.*ต่อ", r"continue", r"resume",
        r"สร้าง.*feature", r"next task", r"task.*ต่อ",
        r"code.*this", r"let.*s.*build", r"start.*coding",
    ],
    "fix": [
        r"\bbug\b", r"พัง", r"\berror\b", r"\bfix\b",
        r"ไม่ทำงาน", r"\bcrash\b", r"exception", r"traceback",
        r"ล้มเหลว", r"broken", r"doesn.*t work", r"not working",
        r"failed", r"failure",
    ],
    "ship": [
        r"\bship\b", r"\brelease\b", r"\bdeploy\b", r"\bpublish\b",
        r"merge.*main", r"go.*live", r"launch", r"ready.*to.*release",
        r"ปล่อย", r"deploy.*now",
    ],
    "retro": [
        r"\bretro\b", r"retrospective", r"สรุป.*session", r"ทบทวน",
        r"review.*session", r"what.*did.*we", r"what.*we.*learned",
        r"what.*worked",
    ],
    "status": [
        r"\bstatus\b", r"ทำอะไรอยู่", r"where.*am.*i", r"progress",
        r"what.*next", r"ต่อไปทำ", r"ถัดไป", r"สถานะ",
    ],
}

SUGGESTIONS = {
    "init":   "/zie-init",
    "idea":   "/zie-idea",
    "plan":   "/zie-plan",
    "build":  "/zie-build",
    "fix":    "/zie-fix",
    "ship":   "/zie-ship",
    "retro":  "/zie-retro",
    "status": "/zie-status",
}

# Score each category
scores = {}
for category, patterns in PATTERNS.items():
    score = 0
    for pattern in patterns:
        if re.search(pattern, message):
            score += 1
    if score > 0:
        scores[category] = score

if not scores:
    sys.exit(0)

# Require at least 1 signal to suggest (lower threshold for common patterns)
best = max(scores, key=scores.get)
best_score = scores[best]

# Only suggest if confident (at least 1 match)
if best_score >= 1:
    cmd = SUGGESTIONS[best]
    # Don't suggest init if already initialized
    if best == "init" and (cwd / "zie-framework" / ".config").exists():
        sys.exit(0)
    print(f"[zie-framework] Detected: {best} intent → {cmd}")
