import pytest
import os
from unittest.mock import patch, MagicMock

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

    @patch('requests.post')
    def test_prepare_workspace_success(self, mock_post, tools):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"workspace_id": "ws-123", "profile": "python", "cache_hit": false}'
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = tools.prepare_workspace("https://github.com/example/repo.git")
        
        assert result == '{"workspace_id": "ws-123", "profile": "python", "cache_hit": false}'
        mock_post.assert_called_once_with(
            "https://docker-vm.crumpton.org:9080/workspaces",
            headers={"Authorization": "Bearer wsd-1783294531376161273", "Content-Type": "application/json"},
            json={"repo_url": "https://github.com/example/repo.git", "ref": "main"},
            timeout=60
        )

    @patch('requests.post')
    def test_prepare_workspace_failure(self, mock_post, tools):
        # Mock failed response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Network error")
        mock_post.return_value = mock_response
        
        result = tools.prepare_workspace("https://github.com/example/repo.git")
        
        assert "Error preparing workspace" in result

    @patch('requests.post')
    def test_exec_command_success(self, mock_post, tools):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"stdout": "test output", "stderr": "", "exit_code": 0, "duration_ms": 100}'
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = tools.exec_command("ws-123", "echo hello", True)
        
        assert result == '{"stdout": "test output", "stderr": "", "exit_code": 0, "duration_ms": 100}'
        mock_post.assert_called_once_with(
            "https://docker-vm.crumpton.org:9080/workspaces/ws-123/exec",
            headers={"Authorization": "Bearer wsd-1783294531376161273", "Content-Type": "application/json"},
            json={
                "command": "echo hello",
                "timeout_seconds": 120,
                "secrets": [],
                "allow_network": True
            },
            timeout=130
        )

    @patch('requests.post')
    def test_exec_command_failure(self, mock_post, tools):
        # Mock failed response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Network error")
        mock_post.return_value = mock_response
        
        result = tools.exec_command("ws-123", "echo hello", True)
        
        assert "Error executing command" in result

    @patch('requests.get')
    def test_get_artifacts_success(self, mock_get, tools):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"diff": "diff --git a/test.py b/test.py\\nindex 123..456\\n--- a/test.py\\n+++ b/test.py\\n@@ -1 +1 @@\\n- test\\n+ new test\\n", "untracked_files": ["new_file.txt"]}'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = tools.get_artifacts("ws-123")
        
        assert result == '{"diff": "diff --git a/test.py b/test.py\\nindex 123..456\\n--- a/test.py\\n+++ b/test.py\\n@@ -1 +1 @@\\n- test\\n+ new test\\n", "untracked_files": ["new_file.txt"]}'
        mock_get.assert_called_once_with(
            "https://docker-vm.crumpton.org:9080/workspaces/ws-123/artifacts",
            headers={"Authorization": "Bearer wsd-1783294531376161273", "Content-Type": "application/json"},
            params={},
            timeout=60
        )

    @patch('requests.get')
    def test_get_artifacts_with_paths(self, mock_get, tools):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"diff": "diff --git a/test.py b/test.py\\nindex 123..456\\n--- a/test.py\\n+++ b/test.py\\n@@ -1 +1 @@\\n- test\\n+ new test\\n", "untracked_files": ["new_file.txt"]}'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = tools.get_artifacts("ws-123", "path/to/file.py")
        
        assert result == '{"diff": "diff --git a/test.py b/test.py\\nindex 123..456\\n--- a/test.py\\n+++ b/test.py\\n@@ -1 +1 @@\\n- test\\n+ new test\\n", "untracked_files": ["new_file.txt"]}'
        mock_get.assert_called_once_with(
            "https://docker-vm.crumpton.org:9080/workspaces/ws-123/artifacts",
            headers={"Authorization": "Bearer wsd-1783294531376161273", "Content-Type": "application/json"},
            params={"paths": "path/to/file.py"},
            timeout=60
        )

    @patch('requests.post')
    def test_commit_and_pr_success(self, mock_post, tools):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"branch_name": "feature-branch", "pr_url": "https://gitlab.com/project/merge_requests/1"}'
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = tools.commit_and_pr("ws-123", "Fix bug", "Bug Fix PR")
        
        assert result == '{"branch_name": "feature-branch", "pr_url": "https://gitlab.com/project/merge_requests/1"}'
        mock_post.assert_called_once_with(
            "https://docker-vm.crumpton.org:9080/workspaces/ws-123/commit-and-pr",
            headers={"Authorization": "Bearer wsd-1783294531376161273", "Content-Type": "application/json"},
            json={
                "commit_message": "Fix bug",
                "pr_title": "Bug Fix PR",
                "pr_description": "",
                "repo_url": ""
            },
            timeout=60
        )

    @patch('requests.get')
    def test_workspace_status_success(self, mock_get, tools):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = '{"status": "running", "created_at": "2023-01-01T00:00:00Z", "last_active": "2023-01-01T00:01:00Z"}'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = tools.workspace_status("ws-123")
        
        assert result == '{"status": "running", "created_at": "2023-01-01T00:00:00Z", "last_active": "2023-01-01T00:01:00Z"}'
        mock_get.assert_called_once_with(
            "https://docker-vm.crumpton.org:9080/workspaces/ws-123/status",
            headers={"Authorization": "Bearer wsd-1783294531376161273", "Content-Type": "application/json"},
            timeout=60
        )

    @patch('requests.delete')
    def test_destroy_workspace_success(self, mock_delete, tools):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = "Workspace ws-123 destroyed."
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        
        result = tools.destroy_workspace("ws-123")
        
        assert result == "Workspace ws-123 destroyed."
        mock_delete.assert_called_once_with(
            "https://docker-vm.crumpton.org:9080/workspaces/ws-123",
            headers={"Authorization": "Bearer wsd-1783294531376161273", "Content-Type": "application/json"},
            timeout=60
        )
