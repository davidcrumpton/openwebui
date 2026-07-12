import pytest
import os

@pytest.fixture
def tools(load_tool):
    # NOTE: gitlab.py reads GITLAB_URL and GITLAB_TOKEN from env vars directly.
    # There are no Valves, so valve_overrides have no effect.
    # Set those env vars to run against a real GitLab instance.
    return load_tool("work_space_daemon/work_space_daemon.py")

class TestWorkSpaceDaemon:

    @pytest.fixture
    def setup_env(self):
        env = os.environ.copy()
        # env["GITLAB_URL"] = "http://localhost:3000"
        # env["GITLAB_TOKEN"] = "dummy_token"
        os.environ.clear()
        os.environ.update(env)
        yield env
        os.environ.clear()
        os.environ.update(env)

    def test_loads(self, tools):
        assert tools is not None

    def test_get_all_repos(self, tools, setup_env):
        result = tools.get_all_repos()
        assert result is not None

    def test_get_projects(self, tools, setup_env):
        result = tools.get_projects()
        assert result is not None

    def test_get_project(self, tools, setup_env):
        result = tools.get_project(1)
        assert result is not None

    def test_get_branches(self, tools, setup_env):
        result = tools.get_branches(1)
        assert result is not None

    def test_get_files(self, tools, setup_env):
        result = tools.get_files(1, "main")
        assert result is not None
    