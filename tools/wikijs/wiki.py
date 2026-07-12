"""
title: WikiJS Tool
author: davidcrumpton
description: >
    WikiJS MCP tools for page management, search, and content operations using GraphQL API.
version: 1.0.0
license: MIT
"""

import os
import json
import requests
from typing import Dict, Any, Optional


class Tools:
    def __init__(self):
        self.base_url = os.getenv(
            "WIKIJS_API_URL",
            "https://your-wiki-url.com",  # Replace with default if necessary
        ).rstrip("/")
        self.api_token = os.getenv("WIKIJS_API_TOKEN")

    # ------------------------------------------------
    # Credential Resolution
    # ------------------------------------------------

    def _get_headers(self, __user__: dict = None) -> dict:
        # Using the provided API token from environment
        token = self.api_token

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------
    # HTTP Layer (GraphQL optimized)
    # ------------------------------------------------

    def _request(
        self,
        method: str,
        url: str,
        json_data: Optional[dict] = None,
        __user__: dict = None,
        timeout: int = 20,
    ) -> Dict[str, Any]:
        """
        Generic request handler for GraphQL POST requests.
        """
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

    # --------------------------------------------------
    # Search Operations
    # --------------------------------------------------

    def search_pages(self, query: str, __user__: dict = None) -> str:
        """
        Search for pages in WikiJS using a query string.
        """
        url = f"{self.base_url}/graphql"
        graphql_query = """
            query SearchPages($query: String!) {
                pages {
                    search(query: $query) {
                        results {
                            id
                            path
                            title
                            locale
                        }
                        suggestions
                        totalHits
                    }
                }
            }
        """

        variables = {"query": query}
        payload = {"query": graphql_query, "variables": variables}

        result = self._request("POST", url, json_data=payload, __user__=__user__)

        if isinstance(result, dict) and "errors" in result:
            return json.dumps(result, indent=2)

        return json.dumps(result, indent=2)

    # --------------------------------------------------
    # Page Retrieval & History
    # --------------------------------------------------

    def get_page(self, page_id: int, __user__: dict = None) -> str:
        """
        Get the content and metadata of a specific page by ID.
        """
        url = f"{self.base_url}/graphql"
        graphql_query = """
          query GetPage($id: Int!) {
            pages {
              single(id: $id) {
                id
                path
                title
                content
                createdAt
                updatedAt
              }
            }
          }
        """

        payload = {"query": graphql_query, "variables": {"id": page_id}}

        result = self._request("POST", url, json_data=payload, __user__=__user__)
        return json.dumps(result, indent=2)

    def get_page_history(self, page_id: int, __user__: dict = None) -> str:
        """
        Get the revision history for a specific page.
        """
        url = f"{self.base_url}/graphql"
        graphql_query = """
          query GetPageHistory($id: Int!) {
            pages {
              single(id: $id) {
                history {
                  id
                  createdAt
                  updatedAt
                  editor {
                    id
                    name
                  }
                }
              }
            }
          }
        """

        payload = {"query": graphql_query, "variables": {"id": page_id}}

        result = self._request("POST", url, json_data=payload, __user__=__user__)
        return json.dumps(result, indent=2)

    # --------------------------------------------------
    # Page Mutation (Create, Update, Delete, Restore)
    # --------------------------------------------------

    def create_page(
        self,
        title: str,
        path: str,
        content: str,
        locale: str = "en",
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Create a new page in WikiJS.
        """
        url = f"{self.base_url}/graphql"
        graphql_mutation = """
          mutation CreatePage($title: String!, $path: String!, $content: String!, $locale: String!) {
            pages {
              create(
                title: $title
                path: $path
                content: $content
                locale: $locale
              ) {
                responseResult {
                  succeeded
                  slug
                  message
                }
                page {
                  id
                  path
                  title
                }
              }
            }
          }
        """

        payload = {
            "query": graphql_mutation,
            "variables": {
                "title": title,
                "path": path,
                "content": content,
                "locale": locale,
            },
        }

        return self._request("POST", url, json_data=payload, __user__=__user__)

    def update_page(
        self,
        page_id: int,
        title: str,
        path: str,
        content: str,
        locale: str = "en",
        __user__: dict = None,
    ) -> Dict[str, Any]:
        """
        Update an existing page.
        """
        url = f"{self.base_url}/graphql"
        graphql_mutation = """
          mutation UpdatePage($id: Int!, $title: String!, $path: String!, $content: String!, $locale: String!) {
            pages {
              update(
                id: $id
                title: $title
                path: $path
                content: $content
                locale: $locale
              ) {
                responseResult {
                  succeeded
                  slug
                  message
                }
                page {
                  id
                  path
                  title
                }
              }
            }
          }
        """

        payload = {
            "query": graphql_mutation,
            "variables": {
                "id": page_id,
                "title": title,
                "path": path,
                "content": content,
                "locale": locale,
            },
        }

        return self._request("POST", url, json_data=payload, __user__=__user__)

    def delete_page(
        self, page_id: int, reason: str = None, __user__: dict = None
    ) -> Dict[str, Any]:
        """
        Delete a page with an optional reason.
        """
        url = f"{self.base_url}/graphql"
        graphql_mutation = """
          mutation DeletePage($id: Int!, $reason: String) {
            pages {
              delete(id: $id, reason: $reason) {
                responseResult {
                  succeeded
                  slug
                  message
                }
              }
            }
          }
        """

        payload = {
            "query": graphql_mutation,
            "variables": {"id": page_id, "reason": reason},
        }

        return self._request("POST", url, json_data=payload, __user__=__user__)

    def restore_page(
        self, page_id: int, revision_id: int, reason: str = None, __user__: dict = None
    ) -> Dict[str, Any]:
        """
        Restore a previous version of a page.
        """
        url = f"{self.base_url}/graphql"
        graphql_mutation = """
          mutation RestorePage($id: Int!, $revisionId: Int!, $reason: String) {
            pages {
              restore(id: $id, revisionId: $token, reason: $reason) {
                responseResult {
                  succeeded
                  slug
                  message
                }
              }
            }
          }
        """
        # Note: In the original JS, variable was revisionId, corrected here for GraphQL consistency
        graphql_mutation = graphql_mutation.replace(
            "revisionId: $token", "revisionId: $revisionId"
        )

        payload = {
            "query": graphql_mutation,
            "variables": {"id": page_id, "revisionId": revision_id, "reason": reason},
        }

        return self._request("POST", url, json_data=payload, __user__=__user__)
