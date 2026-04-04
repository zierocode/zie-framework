import os

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


class TestZieInitDeepScan:
    def test_zie_init_has_existing_project_detection(self):
        content = read("commands/init.md")
        assert "existing" in content.lower(), (
            "zie-init must detect existing vs greenfield projects"
        )

    def test_zie_init_has_agent_explore_scan(self):
        content = read("commands/init.md")
        assert "Agent" in content and "Explore" in content, (
            "zie-init must invoke Agent(subagent_type=Explore) for "
            "existing projects"
        )

    def test_zie_init_updates_knowledge_hash(self):
        content = read("commands/init.md")
        assert "knowledge_hash" in content, (
            "zie-init must compute and store knowledge_hash in .config"
        )

    def test_zie_init_updates_knowledge_synced_at(self):
        content = read("commands/init.md")
        assert "knowledge_synced_at" in content, (
            "zie-init must store knowledge_synced_at in .config"
        )

    def test_zie_init_config_template_has_knowledge_fields(self):
        content = read("commands/init.md")
        assert "knowledge_hash" in content, (
            "zie-init .config must include knowledge_hash field doc"
        )


class TestZieInitSingleScan:
    def test_explore_agent_prompt_includes_migration_candidates(self):
        content = read("commands/init.md")
        assert "migration_candidates" in content, (
            "Explore agent prompt must request migration_candidates in its output"
        )

    def test_no_standalone_step_2h_directory_rescan(self):
        content = read("commands/init.md")
        import re
        old_rescan_pattern = re.compile(
            r"h\.\s+\*\*Detect migratable documentation\*\*.*scan project root",
            re.DOTALL,
        )
        assert not old_rescan_pattern.search(content), (
            "step 2h must not describe a standalone directory rescan; "
            "migration detection must come from the Explore agent report"
        )

    def test_migration_candidates_fallback_on_missing_key(self):
        content = read("commands/init.md")
        assert "missing" in content.lower() or "fallback" in content.lower() or "skip" in content.lower(), (
            "zie-init must document graceful fallback when migration_candidates "
            "is missing or empty from agent report"
        )

    def test_migration_candidates_fallback_on_malformed_json(self):
        content = read("commands/init.md")
        assert (
            "malformed" in content.lower()
            or "garbled" in content.lower()
            or "Could not detect" in content
            or "graceful" in content.lower()
        ), (
            "zie-init must document graceful degradation when agent returns "
            "malformed JSON or omits migration_candidates"
        )

    def test_agent_prompt_includes_backlog_pattern(self):
        content = read("commands/init.md")
        assert "**/backlog/*.md" in content, (
            "Explore agent prompt must include **/backlog/*.md in migration detection patterns"
        )

    def test_agent_prompt_excludes_zie_framework_dir(self):
        content = read("commands/init.md")
        assert "zie-framework/" in content, (
            "Explore agent must still exclude zie-framework/ from scan"
        )

    def test_scan_report_has_existing_hooks_key(self):
        content = read("commands/init.md")
        assert "existing_hooks" in content, (
            "scan_report must include existing_hooks field for hooks install strategy"
        )

    def test_scan_report_has_existing_config_key(self):
        content = read("commands/init.md")
        assert "existing_config" in content, (
            "scan_report must include existing_config field for config preservation strategy"
        )

    def test_scan_report_json_parse_bare_json(self):
        content = read("commands/init.md")
        assert "json.loads" in content or "bare JSON" in content or "strip()" in content, (
            "zie-init must document bare JSON parse strategy for agent output"
        )

    def test_scan_report_json_parse_fallback_extraction(self):
        content = read("commands/init.md")
        assert 'rindex("}")' in content or "last `}`" in content or "rindex" in content or 'first `{`' in content, (
            "zie-init must document fallback JSON extraction (first { to last })"
        )

    def test_step2_line_reduction_marker(self):
        """Step 2 must reference scan_report (compact dispatch) not inline pseudocode."""
        content = read("commands/init.md")
        assert "scan_report" in content, (
            "zie-init Step 2 must reference scan_report returned from agent"
        )

    def test_failure_handling_agent_scan_incomplete(self):
        content = read("commands/init.md")
        assert "Agent scan incomplete" in content or "scan incomplete" in content.lower(), (
            "zie-init must warn 'Agent scan incomplete' on timeout"
        )

    def test_failure_handling_scan_failed(self):
        content = read("commands/init.md")
        assert "Scan failed" in content or "scan failed" in content.lower(), (
            "zie-init must warn 'Scan failed' on non-JSON agent output"
        )

    def test_scan_report_existing_hooks_drives_merge_strategy(self):
        content = read("commands/init.md")
        assert "existing_hooks" in content and "merge" in content.lower(), (
            "zie-init must document that a non-null existing_hooks value drives "
            "a merge strategy for hooks installation (preserve existing handlers)"
        )

    def test_scan_report_existing_config_drives_preserve_strategy(self):
        content = read("commands/init.md")
        assert "existing_config" in content and (
            "preserve" in content.lower() or "user-set" in content.lower()
        ), (
            "zie-init must document that a non-null existing_config value drives "
            "a preserve strategy (read and retain user-set keys before writing)"
        )


class TestZieStatusDriftDetection:
    def test_zie_status_has_knowledge_line(self):
        content = read("commands/status.md")
        assert "Knowledge" in content, (
            "zie-status must include a Knowledge row in status output"
        )

    def test_zie_status_has_drift_detection(self):
        content = read("commands/status.md")
        assert "knowledge_hash" in content or "drift" in content, (
            "zie-status must check knowledge_hash for drift detection"
        )


class TestZieResyncCommand:
    def test_zie_resync_command_exists(self):
        path = os.path.join(REPO_ROOT, "commands", "resync.md")
        assert os.path.exists(path), (
            "commands/resync.md must exist"
        )

    def test_zie_resync_has_agent_explore(self):
        content = read("commands/resync.md")
        assert "Agent" in content and "Explore" in content, (
            "zie-resync must invoke Agent(subagent_type=Explore)"
        )

    def test_zie_resync_updates_hash(self):
        content = read("commands/resync.md")
        assert "knowledge_hash" in content, (
            "zie-resync must update knowledge_hash in .config after resync"
        )
