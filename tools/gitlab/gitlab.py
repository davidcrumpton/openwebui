"""
title: GitLab Tool
author: david crumpton
description: >
    CRUD Calls to manage your GitLab Repo
version: 2.1.0
license: MIT
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

class Tools:
    def __init__(self):
        self.base_url = os.getenv("GITLAB_URL", "https://gitlab.crumpton.org/api/v4")

    # ------------------------------------------------
    # Credential Resolution
    # ------------------------------------------------

    def _fetch_creds(self, username: str) -> Optional[str]:
        env_key = f"GITLAB_TOKEN{username}"
        token = os.getenv(env_key)
        if token:
            return token

        # placeholder for Vault / DB
        # return vault.get(f"gitlab/{username}")

        return os.getenv("GITLAB_TOKEN")

    def _get_headers(self, __user__: dict = None) -> dict:
        username = None

        if isinstance(__user__, dict):
            username = __user__.get("username") or __user__.get("name")

        token = self._fetch_creds(username) if username else os.getenv("GITLAB_TOKEN")

        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------
    # HTTP Layer
    # ------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        json_data: Optional[dict] = None,
        __user__: dict = None,
        timeout: int = 20,
    ) -> Dict[str, Any]:

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(__user__),
                json=json_data,
                timeout=timeout,
            )

            response.raise_for_status()

            if response.text:
                return response.json()

            return {"success": True}

        except requests.exceptions.HTTPError as e:
            return {
                "error": response.status_code,
                "details": response.text,
            }

        except requests.exceptions.RequestException as e:
            return {
                "error": "connection_error",
                "details": str(e),
            }

    # ------------------------------------------------
    # Debug
    # ------------------------------------------------

    def debug_user(self, __user__: dict = {}) -> str:
        return json.dumps(__user__, indent=2, default=str)

    # ------------------------------------------------
    # User helpers
    # ------------------------------------------------

    def _get_username(self, __user__: dict) -> Optional[str]:
        user = __user__ or {}

        username = user.get("username")
        if username:
            return username

        email = user.get("email")
        if email and "@" in email:
            return email.split("@")[0]

        return None

    def _lookup_user_id(self, username: str, __user__: dict = None) -> Optional[int]:

        url = f"{self.base_url}/users?username={quote(username)}"

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return None

        if not isinstance(result, list) or len(result) == 0:
            return None

        return result[0].get("id")

    # ------------------------------------------------
    # Project Lookup (Private Helper)
    # ------------------------------------------------

    def _get_project(
        self,
        project_name: str,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Optional[dict]:
        """
        Retrieve a GitLab project by name, optionally within a specific group.

        Returns the complete project object including:
        - id
        - default_branch
        - path_with_namespace
        - visibility
        - web_url

        Args:
            project_name: The name of the project to find.
            group: Optional group/namespace to search within.
            __user__: User context for authentication.

        Returns:
            The full project dictionary if found, None otherwise.
        """
        # Accept project_name as "group/project" when no explicit group is given.
        # Use GitLab's direct namespace lookup endpoint instead of search, since
        # search only matches the project name, not the full namespaced path.
        if group is None and "/" in project_name:
            encoded = quote(project_name, safe="")
            url = f"{self.base_url}/projects/{encoded}"

            result = self._request("GET", url, __user__=__user__)

            if isinstance(result, dict) and "error" not in result:
                return result

            return None

        if group:
            group_enc = quote(group, safe="")
            url = f"{self.base_url}/groups/{group_enc}/projects?search={quote(project_name)}"
        else:
            url = f"{self.base_url}/projects?search={quote(project_name)}"

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return None

        if not isinstance(result, list):
            return None

        # Case-insensitive exact match first
        for p in result:
            if p.get("name", "").lower() == project_name.lower():
                return p

        # Fallback: if only one result came back, use it
        if len(result) == 1:
            return result[0]

        return None

    # ------------------------------------------------
    # Projects
    # ------------------------------------------------

    def list_projects_by_user(self, __user__: dict = {}) -> str:
        """
        List all projects owned by the current user.

        Returns enriched project information including:
        - id
        - default_branch
        - path_with_namespace
        - visibility
        - web_url
        """
        username = self._get_username(__user__)

        if not username:
            return "Error: Could not determine username."

        user_id = self._lookup_user_id(username, __user__)

        if not user_id:
            return "Error: Could not resolve GitLab user ID."

        url = f"{self.base_url}/users/{user_id}/projects"

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)

        return json.dumps(
            [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "path": r.get("path_with_namespace"),
                    "default_branch": r.get("default_branch"),
                    "visibility": r.get("visibility"),
                    "web_url": r.get("web_url"),
                }
                for r in result
            ],
            indent=2,
        )

    def list_all_projects(self) -> str:
        """
        List all projects visible to the authenticated user.

        Returns enriched project information including:
        - id
        - default_branch
        - path_with_namespace
        - visibility
        - web_url
        """
        url = f"{self.base_url}/projects"
        result = self._request("GET", url)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)

        return json.dumps(
            [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "path": r.get("path_with_namespace"),
                    "default_branch": r.get("default_branch"),
                    "visibility": r.get("visibility"),
                    "web_url": r.get("web_url"),
                }
                for r in result
            ],
            indent=2,
        )

    # ------------------------------------------------
    # Groups
    # ------------------------------------------------

    def list_organizations_by_user(self, __user__: dict = {}) -> str:
        """
        List GitLab Organizations visible to the current user.
        """

        url = f"{self.base_url}/groups"

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)

        return json.dumps(
            [
                {
                    "name": g.get("name"),
                    "path": g.get("full_path"),
                    "description": g.get("description"),
                    "url": g.get("web_url"),
                }
                for g in result
            ],
            indent=2,
        )

    def get_organization_details(self, organization: str, __user__: dict = {}) -> str:
        """
        Get detailed information about a GitLab group/organization.
        """

        if not organization:
            return json.dumps(
                {"status": "error", "error": "organization name is required"}, indent=2
            )

        org_enc = quote(organization, safe="")

        url = f"{self.base_url}/groups/{org_enc}"

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(
                {
                    "status": "error",
                    "error": result.get("error"),
                    "details": result.get("details"),
                },
                indent=2,
            )

        return json.dumps(
            {
                "status": "ok",
                "organization": {
                    "id": result.get("id"),
                    "name": result.get("name"),
                    "path": result.get("full_path"),
                    "description": result.get("description"),
                    "visibility": result.get("visibility"),
                    "web_url": result.get("web_url"),
                    "created_at": result.get("created_at"),
                    "parent_id": result.get("parent_id"),
                },
            },
            indent=2,
        )

    # ------------------------------------------------
    # Group Projects
    # ------------------------------------------------

    def list_projects_by_group(self, group: str, __user__: dict = None) -> str:
        """
        List all projects in a GitLab group.

        Returns enriched project information including:
        - id
        - default_branch
        - path_with_namespace
        - visibility
        - web_url
        """
        group_enc = quote(group, safe="")

        url = f"{self.base_url}/groups/{group_enc}/projects"

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)

        return json.dumps(
            [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "path": r.get("path_with_namespace"),
                    "default_branch": r.get("default_branch"),
                    "visibility": r.get("visibility"),
                    "web_url": r.get("web_url"),
                }
                for r in result
            ],
            indent=2,
        )

    # ------------------------------------------------
    # Project Lookup (Legacy - kept for backward compatibility)
    # ------------------------------------------------

    def _get_project_id(
        self,
        project_name: str,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Optional[int]:
        """
        Legacy helper - returns only the project ID.
        Prefer using _get_project() which returns the full project object.
        """

        if group:
            group_enc = quote(group, safe="")
            url = f"{self.base_url}/groups/{group_enc}/projects?search={quote(project_name)}"
        else:
            url = f"{self.base_url}/projects?search={quote(project_name)}"

        result = self._request("GET", url, __user__=__user__)

        # Catch error responses (dicts with "error" key)
        if isinstance(result, dict):
            return None

        # Case-insensitive exact match first
        for p in result:
            if p.get("name", "").lower() == project_name.lower():
                return p.get("id")

        # Fallback: if only one result came back, it's almost certainly the right one
        if len(result) == 1:
            return result[0].get("id")

        return None

    def get_project_details(
        self,
        project_name: str,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> str:
        """
        Get detailed information about a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Could not find project '{project_name}'.",
                },
                indent=2,
            )

        return json.dumps(project, indent=2)

    def list_files_in_project(
        self,
        project_name: str,
        group: Optional[str] = None,
        path: str = "",
        branch: Optional[str] = None,
        recursive: bool = False,
        __user__: dict = None,
    ) -> str:
        """
        List files and directories in a GitLab repository.

        Args:
            project_name: Project name (e.g. "node")
            group: Optional group/namespace (e.g. "crumptonorg")
            path: Optional subdirectory to list.
            branch: Branch name. Defaults to the project's default branch.
            recursive: Recursively walk the tree.
        """

        project = self._get_project(
            project_name,
            group,
            __user__=__user__,
        )

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Project '{project_name}' not found.",
                },
                indent=2,
            )

        project_id = project["id"]
        ref = branch or project.get("default_branch", "main")

        url = f"{self.base_url}/projects/{project_id}/repository/tree"

        params = {
            "ref": ref,
            "recursive": recursive,
        }

        if path:
            params["path"] = path

        try:
            response = requests.get(
                url,
                headers=self._get_headers(__user__),
                params=params,
                timeout=20,
            )

            response.raise_for_status()
            result = response.json()

            return json.dumps(
                {
                    "status": "ok",
                    "project": project.get("path_with_namespace"),
                    "branch": ref,
                    "path": path or "/",
                    "count": len(result),
                    "files": [
                        {
                            "name": item["name"],
                            "path": item["path"],
                            "type": item["type"],  # blob | tree
                        }
                        for item in result
                    ],
                },
                indent=2,
            )

        except requests.exceptions.HTTPError as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "http_error",
                    "details": str(e),
                    "response": response.text,
                },
                indent=2,
            )

        except requests.exceptions.RequestException as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "request_failed",
                    "details": str(e),
                },
                indent=2,
            )

    def get_file(
        self,
        project_name: str,
        file_path: str,
        group: Optional[str] = None,
        branch: Optional[str] = None,
        __user__: dict = None,
    ) -> str:
        """
        Get raw file contents from a GitLab repository.

        Args:
            project_name: Project name (e.g. "node")
            file_path: Path to the file within the repository
            group: Optional group/namespace (e.g. "crumptonorg")
            branch: Branch name. Defaults to the project's default branch.
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Project '{project_name}' not found.",
                },
                indent=2,
            )

        project_id = project["id"]
        ref = branch or project.get("default_branch", "main")

        encoded_path = quote(file_path, safe="/")

        url = (
            f"{self.base_url}/projects/"
            f"{project_id}/repository/files/"
            f"{encoded_path}/raw"
        )

        params = {"ref": ref}

        try:
            response = requests.get(
                url,
                headers=self._get_headers(__user__),
                params=params,
                timeout=20,
            )

            response.raise_for_status()

            return json.dumps(
                {
                    "status": "ok",
                    "project": project.get("path_with_namespace"),
                    "file_path": file_path,
                    "branch": ref,
                    "content": response.text,
                },
                indent=2,
            )

        except requests.exceptions.HTTPError as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "http_error",
                    "details": str(e),
                    "response": response.text if response else None,
                },
                indent=2,
            )

        except requests.exceptions.RequestException as e:
            return json.dumps(
                {"status": "error", "error": "request_failed", "details": str(e)},
                indent=2,
            )

    def create_file(
        self,
        project_name: str,
        file_path: str,
        content: str,
        group: Optional[str] = None,
        branch: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Create a new file in a GitLab repository.

        Args:
            project_name: Project name (e.g. "node")
            file_path: Path to the file within the repository
            content: Content of the file
            group: Optional group/namespace (e.g. "crumptonorg")
            branch: Branch name. Defaults to the project's default branch.
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]
        ref = branch or project.get("default_branch", "main")

        encoded = quote(file_path, safe="")

        url = f"{self.base_url}/projects/" f"{project_id}/repository/files/{encoded}"

        data = {
            "branch": ref,
            "content": content,
            "commit_message": f"Create {file_path}",
        }

        return self._request("POST", url, data, __user__=__user__)

    def edit_file(
        self,
        project_name: str,
        file_path: str,
        content: str,
        commit_message: str,
        group: Optional[str] = None,
        branch: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Edit an existing file in a GitLab repository.

        Args:
            project_name: Project name (e.g. "node")
            file_path: Path to the file within the repository
            content: New content of the file
            commit_message: Commit message for the change
            group: Optional group/namespace (e.g. "crumptonorg")
            branch: Branch name. Defaults to the project's default branch.
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]
        ref = branch or project.get("default_branch", "main")

        encoded = quote(file_path, safe="")

        url = f"{self.base_url}/projects/" f"{project_id}/repository/files/{encoded}"

        data = {
            "branch": ref,
            "content": content,
            "commit_message": commit_message,
        }

        return self._request("PUT", url, data, __user__=__user__)

    def delete_file(
        self,
        project_name: str,
        file_path: str,
        commit_message: str,
        group: Optional[str] = None,
        branch: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Delete a file from a GitLab repository.

        Args:
            project_name: Project name (e.g. "node")
            file_path: Path to the file within the repository
            commit_message: Commit message for the deletion
            group: Optional group/namespace (e.g. "crumptonorg")
            branch: Branch name. Defaults to the project's default branch.
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]
        ref = branch or project.get("default_branch", "main")

        encoded = quote(file_path, safe="")

        url = f"{self.base_url}/projects/" f"{project_id}/repository/files/{encoded}"

        data = {
            "branch": ref,
            "commit_message": commit_message,
        }

        return self._request("DELETE", url, data, __user__=__user__)

    # ------------------------------------------------
    # Issues
    # ------------------------------------------------
    def list_issues(
        self,
        project_name: str,
        group: Optional[str] = None,
        state: Optional[str] = "opened",
        labels: Optional[str] = None,
        assignee_username: Optional[str] = None,
        __user__: dict = None,
    ) -> str:
        """
        List issues in a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            group: Optional group/namespace (e.g. "crumptonorg")
            state: Issue state ("opened", "closed", "all")
            labels: Optional comma-separated label list
            assignee_username: Optional assignee username
            __user__: User context for authentication.

        Returns:
            JSON string containing matching issues.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Project '{project_name}' not found.",
                },
                indent=2,
            )

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/issues"

        params = {}

        if state:
            params["state"] = state

        if labels:
            params["labels"] = labels

        if assignee_username:
            params["assignee_username"] = assignee_username

        try:
            response = requests.get(
                url,
                headers=self._get_headers(__user__),
                params=params,
                timeout=20,
            )

            response.raise_for_status()

            result = response.json()

            return json.dumps(
                {
                    "status": "ok",
                    "project": project.get("path_with_namespace"),
                    "count": len(result),
                    "issues": [
                        {
                            "iid": issue.get("iid"),
                            "id": issue.get("id"),
                            "title": issue.get("title"),
                            "state": issue.get("state"),
                            "author": issue.get("author", {}).get("username"),
                            "assignees": [
                                a.get("username") for a in issue.get("assignees", [])
                            ],
                            "labels": issue.get("labels", []),
                            "created_at": issue.get("created_at"),
                            "updated_at": issue.get("updated_at"),
                            "web_url": issue.get("web_url"),
                        }
                        for issue in result
                    ],
                },
                indent=2,
            )

        except requests.exceptions.HTTPError as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "http_error",
                    "details": str(e),
                    "response": response.text if "response" in locals() else "",
                },
                indent=2,
            )

        except requests.exceptions.RequestException as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "request_failed",
                    "details": str(e),
                },
                indent=2,
            )

    def create_issue(
        self,
        project_name: str,
        title: str,
        description: str,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Create a new issue in a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            title: Issue title
            description: Issue description
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/issues"

        data = {
            "title": title,
            "description": description,
        }

        return self._request("POST", url, data, __user__=__user__)

    def edit_issue(
        self,
        project_name: str,
        issue_iid: int,
        title: str,
        description: str,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Edit an existing issue in a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            issue_iid: Internal ID of the issue
            title: New issue title
            description: New issue description
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]

        url = f"{self.base_url}/projects/" f"{project_id}/issues/{issue_iid}"

        data = {
            "title": title,
            "description": description,
        }

        return self._request("PUT", url, data, __user__=__user__)

    def create_comment_on_issue(
        self,
        project_name: str,
        issue_iid: int,
        body: str,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue in a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            issue_iid: Internal ID of the issue
            body: Comment text
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]

        url = f"{self.base_url}/projects/" f"{project_id}/issues/{issue_iid}/notes"

        return self._request(
            "POST",
            url,
            {"body": body},
            __user__=__user__,
        )

    def lock_issue(
        self,
        project_name: str,
        issue_iid: int,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Lock an issue in a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            issue_iid: Internal ID of the issue
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]

        url = f"{self.base_url}/projects/" f"{project_id}/issues/{issue_iid}/lock"

        return self._request("POST", url, __user__=__user__)

    # ------------------------------------------------
    # CI/CD Jobs
    # ------------------------------------------------

    def list_jobs(
        self,
        project_name: str,
        group: Optional[str] = None,
        pipeline_id: Optional[int] = None,
        scope: Optional[str] = None,
        status: Optional[str] = None,
        __user__: dict = None,
    ) -> str:
        """
        List CI/CD jobs for a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            group: Optional group/namespace (e.g. "crumptonorg")
            pipeline_id: Optional pipeline ID to filter jobs. If not provided, returns jobs from all pipelines.
            scope: Optional scope to filter jobs (e.g. "test", "build", "deploy").
            status: Optional status to filter jobs (e.g. "failed", "success", "running", "pending", "canceled").
            __user__: User context for authentication.

        Returns:
            JSON string containing job information including id, name, status, stage, duration, and web_url.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Project '{project_name}' not found.",
                },
                indent=2,
            )

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/jobs"

        params = {}
        if pipeline_id:
            params["pipeline_id"] = pipeline_id
        if scope:
            params["scope"] = scope
        if status:
            params["status"] = status

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)

        if not isinstance(result, list):
            return json.dumps(
                {"status": "error", "error": "Unexpected response format"}, indent=2
            )

        return json.dumps(
            {
                "status": "ok",
                "project": project.get("path_with_namespace"),
                "count": len(result),
                "jobs": [
                    {
                        "id": job.get("id"),
                        "name": job.get("name"),
                        "stage": job.get("stage"),
                        "status": job.get("status"),
                        "duration": job.get("duration"),
                        "created_at": job.get("created_at"),
                        "started_at": job.get("started_at"),
                        "finished_at": job.get("finished_at"),
                        "web_url": job.get("web_url"),
                        "failure_reason": job.get("failure_reason"),
                    }
                    for job in result
                ],
            },
            indent=2,
        )

    def get_job(
        self,
        project_name: str,
        job_id: int,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> str:
        """
        Get detailed information about a specific CI/CD job, including failure details.

        Args:
            project_name: Project name (e.g. "node")
            job_id: The numeric job ID (e.g. 7530 from the URL)
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.

        Returns:
            JSON string containing complete job details including failure information, trace log, and metadata.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Project '{project_name}' not found.",
                },
                indent=2,
            )

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/jobs/{job_id}"

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)

        if not isinstance(result, dict):
            return json.dumps(
                {"status": "error", "error": "Unexpected response format"}, indent=2
            )

        return json.dumps(
            {
                "status": "ok",
                "project": project.get("path_with_namespace"),
                "job": {
                    "id": result.get("id"),
                    "name": result.get("name"),
                    "stage": result.get("stage"),
                    "status": result.get("status"),
                    "duration": result.get("duration"),
                    "created_at": result.get("created_at"),
                    "started_at": result.get("started_at"),
                    "finished_at": result.get("finished_at"),
                    "web_url": result.get("web_url"),
                    "failure_reason": result.get("failure_reason"),
                    "tag_list": result.get("tag_list"),
                    "runner": result.get("runner"),
                    "artifacts": result.get("artifacts"),
                    "commit": {
                        "id": (
                            result.get("commit", {}).get("id")
                            if result.get("commit")
                            else None
                        ),
                        "message": (
                            result.get("commit", {}).get("message")
                            if result.get("commit")
                            else None
                        ),
                        "branch": (
                            result.get("commit", {}).get("ref")
                            if result.get("commit")
                            else None
                        ),
                    },
                },
            },
            indent=2,
        )

    def get_job_trace(
        self,
        project_name: str,
        job_id: int,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> str:
        """
        Get the trace log output for a specific CI/CD job.

        Args:
            project_name: Project name (e.g. "node")
            job_id: The numeric job ID
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.

        Returns:
            JSON string containing the job trace log output.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Project '{project_name}' not found.",
                },
                indent=2,
            )

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/jobs/{job_id}/trace"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(__user__),
                timeout=30,
            )

            response.raise_for_status()

            return json.dumps(
                {
                    "status": "ok",
                    "project": project.get("path_with_namespace"),
                    "job_id": job_id,
                    "trace": response.text,
                },
                indent=2,
            )

        except requests.exceptions.HTTPError as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "http_error",
                    "details": str(e),
                    "response": response.text if "response" in locals() else "",
                },
                indent=2,
            )

        except requests.exceptions.RequestException as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "request_failed",
                    "details": str(e),
                },
                indent=2,
            )

    def retry_job(
        self,
        project_name: str,
        job_id: int,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Retry a failed CI/CD job.

        Args:
            project_name: Project name (e.g. "node")
            job_id: The numeric job ID to retry
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.

        Returns:
            Dictionary containing the retried job information.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/jobs/{job_id}/retry"

        return self._request("POST", url, __user__=__user__)

    def cancel_job(
        self,
        project_name: str,
        job_id: int,
        group: Optional[str] = None,
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Cancel a running or pending CI/CD job.

        Args:
            project_name: Project name (e.g. "node")
            job_id: The numeric job ID to cancel
            group: Optional group/namespace (e.g. "crumptonorg")
            __user__: User context for authentication.

        Returns:
            Dictionary containing the canceled job information.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return {
                "status": "error",
                "error": f"Project '{project_name}' not found.",
            }

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/jobs/{job_id}/cancel"

        return self._request("POST", url, __user__=__user__)

    def list_pipelines(
        self,
        project_name: str,
        group: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        __user__: dict = None,
    ) -> str:
        """
        List CI/CD pipelines for a GitLab project.

        Args:
            project_name: Project name (e.g. "node")
            group: Optional group/namespace (e.g. "crumptonorg")
            status: Optional status to filter pipelines (e.g. "failed", "success", "running", "pending", "canceled").
            source: Optional source to filter pipelines (e.g. "push", "web", "schedule", "api").
            __user__: User context for authentication.

        Returns:
            JSON string containing pipeline information.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {
                    "status": "error",
                    "error": f"Project '{project_name}' not found.",
                },
                indent=2,
            )

        project_id = project["id"]

        url = f"{self.base_url}/projects/{project_id}/pipelines"

        params = {}
        if status:
            params["status"] = status
        if source:
            params["source"] = source

        result = self._request("GET", url, __user__=__user__)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)

        if not isinstance(result, list):
            return json.dumps(
                {"status": "error", "error": "Unexpected response format"}, indent=2
            )

        return json.dumps(
            {
                "status": "ok",
                "project": project.get("path_with_namespace"),
                "count": len(result),
                "pipelines": [
                    {
                        "id": pipeline.get("id"),
                        "status": pipeline.get("status"),
                        "source": pipeline.get("source"),
                        "ref": pipeline.get("ref"),
                        "sha": pipeline.get("sha"),
                        "created_at": pipeline.get("created_at"),
                        "updated_at": pipeline.get("updated_at"),
                        "web_url": pipeline.get("web_url"),
                    }
                    for pipeline in result
                ],
            },
            indent=2,
        )

#####################################
# Automation support tools
#####################################
# ------------------------------------------------
    # Merge Request / Branch Hygiene
    # ------------------------------------------------

    @staticmethod
    def _parse_gitlab_ts(ts: str) -> Optional[datetime]:
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return None

    def find_stale_merge_requests(
        self,
        project_name: str,
        group: Optional[str] = None,
        days: int = 30,
        state: str = "opened",
        __user__: dict = None,
    ) -> str:
        """
        Find merge requests that haven't been updated in over `days` days.

        Args:
            project_name: Project name (e.g. "node")
            group: Optional group/namespace (e.g. "crumptonorg")
            days: Staleness threshold in days (default 30)
            state: MR state to check ("opened", "closed", "merged", "all")
            __user__: User context for authentication.

        Returns:
            JSON string with stale MRs, sorted oldest-updated first.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {"status": "error", "error": f"Project '{project_name}' not found."},
                indent=2,
            )

        project_id = project["id"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        url = f"{self.base_url}/projects/{project_id}/merge_requests"
        params = {
            "state": state,
            "order_by": "updated_at",
            "sort": "asc",
            "per_page": 100,
        }

        stale = []
        page = 1
        max_pages = 20  # safety cap

        try:
            while page <= max_pages:
                params["page"] = page

                response = requests.get(
                    url,
                    headers=self._get_headers(__user__),
                    params=params,
                    timeout=20,
                )
                response.raise_for_status()
                batch = response.json()

                if not batch:
                    break

                stop = False
                for mr in batch:
                    updated = self._parse_gitlab_ts(mr.get("updated_at"))
                    if updated is None:
                        continue
                    if updated >= cutoff:
                        # sorted asc by updated_at -> everything after this is newer
                        stop = True
                        break
                    stale.append(
                        {
                            "iid": mr.get("iid"),
                            "title": mr.get("title"),
                            "author": mr.get("author", {}).get("username"),
                            "source_branch": mr.get("source_branch"),
                            "target_branch": mr.get("target_branch"),
                            "state": mr.get("state"),
                            "created_at": mr.get("created_at"),
                            "updated_at": mr.get("updated_at"),
                            "days_stale": (
                                datetime.now(timezone.utc) - updated
                            ).days,
                            "web_url": mr.get("web_url"),
                        }
                    )

                if stop or len(batch) < params["per_page"]:
                    break

                page += 1

            return json.dumps(
                {
                    "status": "ok",
                    "project": project.get("path_with_namespace"),
                    "threshold_days": days,
                    "count": len(stale),
                    "merge_requests": stale,
                },
                indent=2,
            )

        except requests.exceptions.HTTPError as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "http_error",
                    "details": str(e),
                    "response": response.text if "response" in locals() else "",
                },
                indent=2,
            )

        except requests.exceptions.RequestException as e:
            return json.dumps(
                {"status": "error", "error": "request_failed", "details": str(e)},
                indent=2,
            )

    def find_old_branches(
        self,
        project_name: str,
        group: Optional[str] = None,
        days: int = 30,
        exclude_default: bool = True,
        exclude_protected: bool = False,
        __user__: dict = None,
    ) -> str:
        """
        Find branches whose last commit is older than `days` days.

        Args:
            project_name: Project name (e.g. "node")
            group: Optional group/namespace (e.g. "crumptonorg")
            days: Staleness threshold in days (default 30)
            exclude_default: Skip the project's default branch (default True)
            exclude_protected: Skip protected branches (default False)
            __user__: User context for authentication.

        Returns:
            JSON string with old branches, sorted oldest-commit first.
        """

        project = self._get_project(project_name, group, __user__=__user__)

        if not project:
            return json.dumps(
                {"status": "error", "error": f"Project '{project_name}' not found."},
                indent=2,
            )

        project_id = project["id"]
        default_branch = project.get("default_branch")
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        url = f"{self.base_url}/projects/{project_id}/repository/branches"
        params = {"per_page": 100}

        old = []
        page = 1
        max_pages = 20  # safety cap

        try:
            while page <= max_pages:
                params["page"] = page

                response = requests.get(
                    url,
                    headers=self._get_headers(__user__),
                    params=params,
                    timeout=20,
                )
                response.raise_for_status()
                batch = response.json()

                if not batch:
                    break

                for branch in batch:
                    name = branch.get("name")

                    if exclude_default and name == default_branch:
                        continue
                    if exclude_protected and branch.get("protected"):
                        continue

                    commit = branch.get("commit") or {}
                    committed = self._parse_gitlab_ts(commit.get("committed_date"))

                    if committed is None or committed >= cutoff:
                        continue

                    old.append(
                        {
                            "name": name,
                            "protected": branch.get("protected"),
                            "merged": branch.get("merged"),
                            "last_commit_sha": commit.get("short_id"),
                            "last_commit_author": commit.get("author_name"),
                            "last_commit_message": commit.get("title"),
                            "committed_date": commit.get("committed_date"),
                            "days_stale": (
                                datetime.now(timezone.utc) - committed
                            ).days,
                            "web_url": f"{project.get('web_url')}/-/tree/{quote(name, safe='')}",
                        }
                    )

                if len(batch) < params["per_page"]:
                    break

                page += 1

            old.sort(key=lambda b: b["days_stale"], reverse=True)

            return json.dumps(
                {
                    "status": "ok",
                    "project": project.get("path_with_namespace"),
                    "threshold_days": days,
                    "count": len(old),
                    "branches": old,
                },
                indent=2,
            )

        except requests.exceptions.HTTPError as e:
            return json.dumps(
                {
                    "status": "error",
                    "error": "http_error",
                    "details": str(e),
                    "response": response.text if "response" in locals() else "",
                },
                indent=2,
            )

        except requests.exceptions.RequestException as e:
            return json.dumps(
                {"status": "error", "error": "request_failed", "details": str(e)},
                indent=2,
            )