"""
title: Workspace Daemon (wsd)
description: Prepare ephemeral dev workspaces, run commands, pull diffs, and tear down via the local wsd Go daemon.
version: 0.2.1
"""

import requests
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        base_url: str = Field(
            default="https://docker-vm.crumpton.org:9080",
            description="Base URL of the wsd daemon.",
        )
        token: str = Field(
            default="wsd-1783294531376161273",
            description="Bearer token printed by wsd on startup (WSD_TOKEN or the auto-generated one).",
        )
        timeout_seconds: int = Field(
            default=60,
            description="Default HTTP timeout for daemon requests.",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.valves.token}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.valves.base_url.rstrip('/')}{path}"

    def prepare_workspace(self, repo_url: str, ref: str = "main") -> str:
        """
        Provision a new ephemeral workspace from a git repo. Detects language/package
        manager automatically and installs dependencies (using cache if available).

        :param repo_url: Git URL to clone (https or ssh).
        :param ref: Branch, tag, or commit to check out. Defaults to "main".
        :return: JSON string with workspace_id, detected environment profile, and cache_hit.
        """
        try:
            resp = requests.post(
                self._url("/workspaces"),
                headers=self._headers(),
                json={"repo_url": repo_url, "ref": ref},
                timeout=self.valves.timeout_seconds,
            )
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            return f"Error preparing workspace: {e}"

    def exec_command(
        self,
        workspace_id: str,
        command: str,
        allow_network: bool,
        timeout_seconds: int = 120,
        secrets: list[str] = [],
    ) -> str:
        """
        Run a shell command inside an existing workspace and return its output.

        :param workspace_id: ID returned by prepare_workspace.
        :param command: Shell command to execute, e.g. "go test ./..." or "pytest".
        :param allow_network: MANDATORY: Set to True if this command needs internet access.
                              Set to False for local tasks to enhance security.
        :param timeout_seconds: Max seconds to allow the command to run before it's killed.
        :param secrets: List of secret reference names to grant for this exec call only.
        :return: JSON string with stdout, stderr, exit_code, and duration_ms.
        """
        try:
            resp = requests.post(
                self._url(f"/workspaces/{workspace_id}/exec"),
                headers=self._headers(),
                json={
                    "command": command,
                    "timeout_seconds": timeout_seconds,
                    "secrets": secrets,
                    "allow_network": allow_network,
                },
                timeout=timeout_seconds + 10,
            )
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            return f"Error executing command: {e}"

    def get_artifacts(self, workspace_id: str, paths: str = "") -> str:
        """
        Retrieve a diff-patch of uncommitted changes made inside the workspace,
        plus any new untracked files, without pushing or committing anything.

        :param workspace_id: ID returned by prepare_workspace.
        :param paths: Optional comma-separated list of paths to scope the diff to.
        :return: JSON string with the unified diff patch and untracked file list.
        """
        try:
            params = {"paths": paths} if paths else {}
            resp = requests.get(
                self._url(f"/workspaces/{workspace_id}/artifacts"),
                headers=self._headers(),
                params=params,
                timeout=self.valves.timeout_seconds,
            )
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            return f"Error fetching artifacts: {e}"

    def commit_and_pr(
        self,
        workspace_id: str,
        commit_message: str,
        pr_title: str,
        pr_description: str = "",
        repo_url: str = "",
        gitlab_project_path: str = "",
    ) -> str:
        """
        Commit the workspace's current changes and open a GitLab merge request.
        The branch name is chosen by the daemon, not the model - this can only
        ever create a new branch, never overwrite an existing one or push to
        main directly. Call this once the task is complete and tested.

        :param workspace_id: ID returned by prepare_workspace.
        :param commit_message: Git commit message for the changes.
        :param pr_title: Title for the merge request.
        :param pr_description: Optional longer description for the merge request.
        :param repo_url: Repository URL to push to.
        :param gitlab_project_path: URL-encoded namespace/project path, or numeric project ID.
        :return: JSON string with the branch name and merge request URL, or an error.

        """
        try:
            payload = {
                "commit_message": commit_message,
                "pr_title": pr_title,
                "pr_description": pr_description,
                "repo_url": repo_url,
            }
            if gitlab_project_path:
                payload["gitlab_project_path"] = gitlab_project_path
            
            resp = requests.post(
                self._url(f"/workspaces/{workspace_id}/commit-and-pr"),
                headers=self._headers(),
                json=payload,
                timeout=self.valves.timeout_seconds,
            )
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            return f"Error committing and opening PR: {e}"

    def workspace_status(self, workspace_id: str) -> str:
        """
        Check whether a workspace is alive and healthy.

        :param workspace_id: ID returned by prepare_workspace.
        :return: JSON string with status info.
        """
        try:
            resp = requests.get(
                self._url(f"/workspaces/{workspace_id}/status"),
                headers=self._headers(),
                timeout=self.valves.timeout_seconds,
            )
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.RequestException as e:
            return f"Error fetching status: {e}"

    def destroy_workspace(self, workspace_id: str) -> str:
        """
        Tear down a workspace and free its resources. Call this when done with a task.

        :param workspace_id: ID returned by prepare_workspace.
        :return: Confirmation or error message.
        """
        try:
            resp = requests.delete(
                self._url(f"/workspaces/{workspace_id}"),
                headers=self._headers(),
                timeout=self.valves.timeout_seconds,
            )
            resp.raise_for_status()
            return f"Workspace {workspace_id} destroyed."
        except requests.exceptions.RequestException as e:
            return f"Error destroying workspace: {e}"