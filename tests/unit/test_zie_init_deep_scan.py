import os

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


class TestZieInitDeepScan:
    def test_zie_init_has_existing_project_detection(self):
        content = read("commands/zie-init.md")
        assert "existing" in content.lower(), (
            "zie-init must detect existing vs greenfield projects"
        )

    def test_zie_init_has_agent_explore_scan(self):
        content = read("commands/zie-init.md")
        assert "Agent" in content and "Explore" in content, (
            "zie-init must invoke Agent(subagent_type=Explore) for "
            "existing projects"
        )

    def test_zie_init_updates_knowledge_hash(self):
        content = read("commands/zie-init.md")
        assert "knowledge_hash" in content, (
            "zie-init must compute and store knowledge_hash in .config"
        )

    def test_zie_init_updates_knowledge_synced_at(self):
        content = read("commands/zie-init.md")
        assert "knowledge_synced_at" in content, (
            "zie-init must store knowledge_synced_at in .config"
        )

    def test_zie_init_config_template_has_knowledge_fields(self):
        content = read("commands/zie-init.md")
        assert "knowledge_hash" in content, (
            "zie-init .config must include knowledge_hash field doc"
        )


class TestZieInitSingleScan:
    def test_explore_agent_prompt_includes_migratable_docs(self):
        content = read("commands/zie-init.md")
        assert "migratable_docs" in content, (
            "Explore agent prompt must request migratable_docs in its output"
        )

    def test_no_standalone_step_2h_directory_rescan(self):
        content = read("commands/zie-init.md")
        import re
        old_rescan_pattern = re.compile(
            r"h\.\s+\*\*Detect migratable documentation\*\*.*scan project root",
            re.DOTALL,
        )
        assert not old_rescan_pattern.search(content), (
            "step 2h must not describe a standalone directory rescan; "
            "migration detection must come from the Explore agent report"
        )

    def test_migratable_docs_fallback_on_missing_key(self):
        content = read("commands/zie-init.md")
        assert "missing" in content.lower() or "fallback" in content.lower() or "skip" in content.lower(), (
            "zie-init must document graceful fallback when migratable_docs "
            "is missing or empty from agent report"
        )

    def test_migratable_docs_fallback_on_malformed_json(self):
        content = read("commands/zie-init.md")
        assert (
            "malformed" in content.lower()
            or "garbled" in content.lower()
            or "Could not detect" in content
            or "graceful" in content.lower()
        ), (
            "zie-init must document graceful degradation when agent returns "
            "malformed JSON or omits migratable_docs"
        )

    def test_agent_prompt_includes_backlog_pattern(self):
        content = read("commands/zie-init.md")
        assert "**/backlog/*.md" in content, (
            "Explore agent prompt must include **/backlog/*.md in migration detection patterns"
        )

    def test_agent_prompt_excludes_zie_framework_dir(self):
        content = read("commands/zie-init.md")
        assert "zie-framework/" in content, (
            "Explore agent must still exclude zie-framework/ from scan"
        )


class TestZieStatusDriftDetection:
    def test_zie_status_has_knowledge_line(self):
        content = read("commands/zie-status.md")
        assert "Knowledge" in content, (
            "zie-status must include a Knowledge row in status output"
        )

    def test_zie_status_has_drift_detection(self):
        content = read("commands/zie-status.md")
        assert "knowledge_hash" in content or "drift" in content, (
            "zie-status must check knowledge_hash for drift detection"
        )


class TestZieResyncCommand:
    def test_zie_resync_command_exists(self):
        path = os.path.join(REPO_ROOT, "commands", "zie-resync.md")
        assert os.path.exists(path), (
            "commands/zie-resync.md must exist"
        )

    def test_zie_resync_has_agent_explore(self):
        content = read("commands/zie-resync.md")
        assert "Agent" in content and "Explore" in content, (
            "zie-resync must invoke Agent(subagent_type=Explore)"
        )

    def test_zie_resync_updates_hash(self):
        content = read("commands/zie-resync.md")
        assert "knowledge_hash" in content, (
            "zie-resync must update knowledge_hash in .config after resync"
        )
