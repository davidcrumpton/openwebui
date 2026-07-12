"""
title: Home Assistant Tool
author: David Crumpton
description: >
    Control and query Home Assistant via its REST API. Supports getting/setting entity states,
    calling services, firing events, listing calendars, rendering templates, and more.
version: 1.0.0
license: MIT
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from urllib.parse import quote, urljoin


class Tools:
    def __init__(self):
        self.base_url = os.getenv("HASS_URL", "http://homeassistant.local:8123")
        self.api_token = os.getenv("HASS_TOKEN")

    # --- Internal Helpers ---

    def _get_headers(self) -> dict:
        if not self.api_token:
            return {
                "Content-Type": "application/json",
            }
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: int = 20,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=json_data,
                params=params,
                timeout=timeout,
            )

            # Handle 204 No Content or empty responses
            if response.status_code == 204 or not response.text.strip():
                return {"success": True, "result": None}

            # Try to parse JSON
            try:
                result = response.json()
            except json.JSONDecodeError:
                # Fallback to plain text (e.g., for error_log or templates)
                result = response.text

            response.raise_for_status()
            return {"success": True, "result": result}

        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "details": response.text,
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": "connection_error",
                "details": str(e),
            }

    # --- API Actions ---

    def ping(self) -> str:
        """Health check: Ping the Home Assistant API."""
        result = self._request("GET", "/api/")
        return json.dumps(result, indent=2)

    def get_config(self) -> str:
        """Get current Home Assistant configuration."""
        result = self._request("GET", "/api/config")
        return json.dumps(result, indent=2)

    def get_states(self) -> str:
        """Get all entity states."""
        result = self._request("GET", "/api/states")
        return json.dumps(result, indent=2)

    def get_state(self, entity_id: str) -> str:
        """Get the state of a specific entity."""
        encoded_id = quote(entity_id, safe="")
        result = self._request("GET", f"/api/states/{encoded_id}")
        return json.dumps(result, indent=2)

    def set_state(
        self, entity_id: str, state: str, attributes: Optional[dict] = None
    ) -> str:
        """Set the state and attributes of an entity."""
        encoded_id = quote(entity_id, safe="")
        body = {"state": state}
        if attributes:
            body["attributes"] = attributes

        result = self._request("POST", f"/api/states/{encoded_id}", json_data=body)
        return json.dumps(result, indent=2)

    def delete_state(self, entity_id: str) -> str:
        """Delete the state of an entity."""
        encoded_id = quote(entity_id, safe="")
        result = self._request("DELETE", f"/api/states/{encoded_id}")
        return json.dumps(result, indent=2)

    def get_services(self) -> str:
        """List all available services."""
        result = self._request("GET", "/api/services")
        return json.dumps(result, indent=2)

    def call_service(
        self,
        domain: str,
        service: str,
        service_data: Optional[dict] = None,
        return_response: bool = False,
    ) -> str:
        """Call a specific service."""
        path = f"/api/services/{quote(domain, safe='')}/{quote(service, safe='')}"
        if return_response:
            path += "?return_response"

        result = self._request("POST", path, json_data=service_data or {})
        return json.dumps(result, indent=2)

    def get_events(self) -> str:
        """Get recent events."""
        result = self._request("GET", "/api/events")
        return json.dumps(result, indent=2)

    def fire_event(self, event_type: str, event_data: Optional[dict] = None) -> str:
        """Fire a custom event."""
        path = f"/api/events/{quote(event_type, safe='')}"
        result = self._request("POST", path, json_data=event_data or {})
        return json.dumps(result, indent=2)

    def get_history(
        self,
        entity_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        minimal_response: bool = False,
        no_attributes: bool = False,
        significant_changes_only: bool = False,
    ) -> str:
        """Get history for an entity within a time period."""
        path = "/api/history/period"
        if start_time:
            path += f"/{quote(start_time, safe='')}"

        params = {"filter_entity_id": entity_id}
        if end_time:
            params["end_time"] = end_time
        if minimal_response:
            params["minimal_response"] = "true"
        if no_attributes:
            params["no_attributes"] = "true"
        if significant_changes_only:
            params["significant_changes_only"] = "true"

        result = self._request("GET", path, params=params)
        return json.dumps(result, indent=2)

    def get_logbook(
        self,
        entity_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> str:
        """Get logbook entries."""
        path = "/api/logbook"
        if start_time:
            path += f"/{quote(start_time, safe='')}"
        params = {}
        if entity_id:
            params["entity"] = entity_id
        if end_time:
            params["end_time"] = end_time
        result = self._request("GET", path, params=params)
        return json.dumps(result, indent=2)

    def get_calendars(self) -> str:
        """List all available calendars."""
        result = self._request("GET", "/api/calendars")
        return json.dumps(result, indent=2)

    def get_calendar_events(self, calendar_entity_id: str, start: str, end: str) -> str:
        """Get events from a specific calendar."""
        encoded_id = quote(calendar_entity_id, safe="")
        params = {"start": start, "end": end}
        path = f"/api/calendars/{encoded_id}"
        result = self._request("GET", path, params=params)
        return json.dumps(result, indent=2)

    def render_template(self, template: str) -> str:
        """Render a Jinja2 template via Home Assistant."""
        result = self._request(
            "POST", "/api/template", json_data={"template": template}
        )
        return json.dumps(result, indent=2)

    def get_error_log(self) -> str:
        """Fetch the Home Assistant error log."""
        result = self._request("GET", "/api/error_log")
        return json.dumps(result, indent=2)

    def check_config(self) -> str:
        """Check the validity of the Home Assistant configuration."""
        result = self._request("POST", "/api/config/core/check_config")
        return json.dumps(result, indent=2)
