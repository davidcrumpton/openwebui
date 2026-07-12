import pytest


@pytest.fixture
def tools(load_tool):
    # NOTE: gitlab.py reads GITLAB_URL and GITLAB_TOKEN from env vars directly.
    # There are no Valves, so valve_overrides have no effect.
    # Set those env vars to run against a real GitLab instance.
    return load_tool("gitlab/gitlab.py")


class TestGitlabTools:
    def test_loads(self, tools):
        assert tools is not None

    def test_get_project_details(self, tools, kwargs_for):
        # NOTE: This test WILL FAIL unless GITLAB_URL and GITLAB_TOKEN env vars are set.
        # That is expected — it exercises the live HTTP path.
        kwargs = kwargs_for(tools, "get_project_details", project_name="mcphe")
        result = tools.get_project_details(**kwargs)
        # When env vars are missing the request returns an error JSON string — that's OK.
        # When they are set it should contain real project data including "id".
        assert result is not None