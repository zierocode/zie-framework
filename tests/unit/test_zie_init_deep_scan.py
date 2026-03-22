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
