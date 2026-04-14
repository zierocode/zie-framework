#!/usr/bin/env python3
"""
docs-sync-check — Verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk.
"""

import json
import os
import re
import sys
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    # The skill runs from the project root
    return Path.cwd()


def glob_commands(project_root):
    """Get all command files from commands/*.md"""
    commands_dir = project_root / "commands"
    if not commands_dir.exists():
        return set()
    return {f.stem for f in commands_dir.glob("*.md")}


def glob_skills(project_root):
    """Get all skill directories from skills/*/SKILL.md"""
    skills_dir = project_root / "skills"
    if not skills_dir.exists():
        return set()
    return {d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()}


def glob_hooks(project_root):
    """Get all hook files from hooks/*.py (exclude utils*.py)"""
    hooks_dir = project_root / "hooks"
    if not hooks_dir.exists():
        return set()
    hooks = set()
    for f in hooks_dir.glob("*.py"):
        if f.name.startswith("utils"):
            continue
        hooks.add(f.stem)
    return hooks


def read_file_safe(path):
    """Read file contents safely."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def extract_claude_md_mentions(content):
    """Extract lines mentioning commands/, skills/, hooks/ from CLAUDE.md."""
    if not content:
        return None

    mentions = set()
    for line in content.split("\n"):
        # Look for paths like commands/*.md, skills/*/SKILL.md, hooks/*.py
        if "commands/" in line:
            mentions.add("commands/")
        if "skills/" in line:
            mentions.add("skills/")
        if "hooks/" in line:
            mentions.add("hooks/")
    return mentions


def extract_readme_commands_table(content):
    """Extract command names from README.md commands table."""
    if not content:
        return None

    commands = set()
    in_commands_table = False

    for line in content.split("\n"):
        # Detect commands table header
        if "| Command" in line and "| Stage" in line:
            in_commands_table = True
            continue
        # Detect end of table (empty line or different header)
        if in_commands_table and (line.strip() == "" or line.startswith("##")):
            break
        # Parse command rows
        if in_commands_table and line.strip().startswith("| `/"):
            match = re.match(r"\| `/([^`]+)`", line)
            if match:
                commands.add(match.group(1))

    return commands


def extract_project_md_tables(content):
    """Extract Commands and Skills tables from PROJECT.md."""
    if not content:
        return None, None

    commands = set()
    skills = set()
    in_commands_table = False
    in_skills_table = False

    for line in content.split("\n"):
        # Detect Commands table header
        if "| Command" in line and "| Description" in line:
            in_commands_table = True
            in_skills_table = False
            continue
        # Detect Skills table header
        if "| Skill" in line and "| Purpose" in line:
            in_skills_table = True
            in_commands_table = False
            continue
        # Detect end of tables (## header or empty line after being in table)
        if line.startswith("##"):
            in_commands_table = False
            in_skills_table = False
            continue

        # Skip header separator row
        if line.strip().startswith("| ---"):
            continue

        # Parse Commands table rows (format: | /command | description |)
        if in_commands_table and line.strip().startswith("| /"):
            match = re.match(r"\| /([^|]+)\|", line)
            if match:
                cmd = match.group(1).strip()
                commands.add(cmd)

        # Parse Skills table rows (format: | skill-name | description |)
        if in_skills_table and line.strip().startswith("| "):
            match = re.match(r"\| ([a-zA-Z][^|]*)\|", line)
            if match:
                skill = match.group(1).strip()
                # Skip header rows
                if skill.lower() in ("skill", "---"):
                    continue
                skills.add(skill)

    return commands, skills


def run_sync_check(changed_files=None):
    """Run the full sync check."""
    project_root = get_project_root()

    # Read documentation files
    claude_md_content = read_file_safe(project_root / "CLAUDE.md")
    readme_content = read_file_safe(project_root / "README.md")
    project_md_content = read_file_safe(project_root / "zie-framework" / "PROJECT.md")

    # Get actual state from disk
    actual_commands = glob_commands(project_root)
    actual_skills = glob_skills(project_root)
    actual_hooks = glob_hooks(project_root)

    # Initialize results
    results = {
        "claude_md_stale": False,
        "readme_stale": False,
        "project_md_stale": False,
        "missing_from_docs": [],
        "extra_in_docs": [],
        "missing_from_project_md": [],
        "extra_in_project_md": [],
        "details": []
    }

    # Check CLAUDE.md
    claude_md_mentions = extract_claude_md_mentions(claude_md_content)
    if not claude_md_mentions:
        results["details"].append("CLAUDE.md not found or no commands/skills/hooks mentions")
        results["claude_md_stale"] = False
    else:
        # CLAUDE.md just needs to mention the directories, not list every file
        # So we just check if it mentions all three categories
        if "commands/" in claude_md_mentions and "skills/" in claude_md_mentions and "hooks/" in claude_md_mentions:
            results["details"].append("CLAUDE.md in sync")
        else:
            missing_mentions = []
            if "commands/" not in claude_md_mentions:
                missing_mentions.append("commands/")
            if "skills/" not in claude_md_mentions:
                missing_mentions.append("skills/")
            if "hooks/" not in claude_md_mentions:
                missing_mentions.append("hooks/")
            results["details"].append(f"CLAUDE.md missing mentions: {', '.join(missing_mentions)}")
            results["claude_md_stale"] = True

    # Check README.md commands table
    readme_commands = extract_readme_commands_table(readme_content)
    if readme_commands is None:
        results["details"].append("README.md not found or no commands table")
        results["readme_stale"] = False
    else:
        missing_from_readme = actual_commands - readme_commands
        extra_in_readme = readme_commands - actual_commands

        if missing_from_readme:
            results["missing_from_docs"].extend([f"commands/{c}" for c in sorted(missing_from_readme)])
            results["readme_stale"] = True
        if extra_in_readme:
            results["extra_in_docs"].extend([f"commands/{c}" for c in sorted(extra_in_readme)])
            results["readme_stale"] = True

        if not missing_from_readme and not extra_in_readme:
            results["details"].append("README.md in sync")
        else:
            if missing_from_readme:
                results["details"].append(f"README.md missing commands: {', '.join(sorted(missing_from_readme))}")
            if extra_in_readme:
                results["details"].append(f"README.md has extra commands: {', '.join(sorted(extra_in_readme))}")

    # Check PROJECT.md tables
    project_commands, project_skills = extract_project_md_tables(project_md_content)
    if project_commands is None or project_md_content is None:
        results["details"].append("PROJECT.md not found — skipped")
        results["project_md_stale"] = False
    else:
        # Check commands
        missing_commands = actual_commands - project_commands
        extra_commands = project_commands - actual_commands

        # Check skills
        missing_skills = actual_skills - project_skills
        extra_skills = project_skills - actual_skills

        if missing_commands:
            results["missing_from_project_md"].extend([f"commands/{c}" for c in sorted(missing_commands)])
            results["project_md_stale"] = True
        if extra_commands:
            results["extra_in_project_md"].extend([f"commands/{c}" for c in sorted(extra_commands)])
            results["project_md_stale"] = True
        if missing_skills:
            results["missing_from_project_md"].extend([f"skills/{s}" for s in sorted(missing_skills)])
            results["project_md_stale"] = True
        if extra_skills:
            results["extra_in_project_md"].extend([f"skills/{s}" for s in sorted(extra_skills)])
            results["project_md_stale"] = True

        if not missing_commands and not extra_commands and not missing_skills and not extra_skills:
            results["details"].append("PROJECT.md in sync")
        else:
            if missing_commands:
                results["details"].append(f"PROJECT.md missing commands: {', '.join(sorted(missing_commands))}")
            if extra_commands:
                results["details"].append(f"PROJECT.md has extra commands: {', '.join(sorted(extra_commands))}")
            if missing_skills:
                results["details"].append(f"PROJECT.md missing skills: {', '.join(sorted(missing_skills))}")
            if extra_skills:
                results["details"].append(f"PROJECT.md has extra skills: {', '.join(sorted(extra_skills))}")

    # Convert details list to string
    results["details"] = " | ".join(results["details"]) if results["details"] else "No issues found"

    return results


def main():
    """Main entry point."""
    # Parse arguments
    changed_files = None
    if len(sys.argv) > 1:
        try:
            args = json.loads(sys.argv[1])
            changed_files = args.get("changed_files", [])
        except json.JSONDecodeError:
            pass

    # Run check
    results = run_sync_check(changed_files)

    # Output JSON
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
