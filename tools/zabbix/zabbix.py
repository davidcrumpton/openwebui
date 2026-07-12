"""
title: Zabbix Tool
author: davidcrumpton
description: >
    Zabbix MCP tools for zabbix management
version: 1.0.0
license: MIT
"""

import json
import os
import requests
from pydantic import BaseModel, Field
from typing import Optional


class Tools:
    class Valves(BaseModel):
        ZABBIX_API_URL: str = Field(
            default="",
            description="Zabbix API URL (e.g. http://zabbix.example.com/api_jsonrpc.php)",
        )
        ZABBIX_AUTH_TOKEN: str = Field(
            default="",
            description="Zabbix API auth token (preferred over username/password)",
        )
        ZABBIX_USER: str = Field(
            default="",
            description="Zabbix username (used only if auth token is not set)",
        )
        ZABBIX_PASSWORD: str = Field(
            default="",
            description="Zabbix password (used only if auth token is not set)",
        )

    def __init__(self):
        self.valves = self.Valves()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _api_url(self) -> str:
        return os.environ.get("ZABBIX_API_URL") or self.valves.ZABBIX_API_URL

    def _auth_token(self) -> str:
        return os.environ.get("ZABBIX_AUTH_TOKEN") or self.valves.ZABBIX_AUTH_TOKEN

    def _rpc(self, method: str, params: dict, use_auth: bool = True) -> dict:
        """Send a Zabbix JSON-RPC request and return the parsed response dict."""
        api_url = self._api_url()
        if not api_url:
            return {"success": False, "error": "ZABBIX_API_URL is not configured"}

        body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }

        if use_auth:
            token = self._auth_token()
            body["auth"] = token if token else None

        try:
            response = requests.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "openwebui-zabbix-tools/1.0",
                },
                data=json.dumps(body),
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            return {"success": False, "error": f"HTTP error: {e}"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse response: {e}"}

        if "error" in data:
            return {"success": False, "error": data["error"]}

        return {"success": True, "result": data.get("result")}

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def zabbix_login(self) -> str:
        """
        Authenticate with the Zabbix API using configured username and password.
        Returns an auth token that can be used for subsequent calls.
        Use this only when an auth token is not already configured.
        """
        username = os.environ.get("ZABBIX_USER") or self.valves.ZABBIX_USER
        password = os.environ.get("ZABBIX_PASSWORD") or self.valves.ZABBIX_PASSWORD

        if not username or not password:
            return json.dumps(
                {
                    "success": False,
                    "error": "ZABBIX_USER and ZABBIX_PASSWORD must be configured to use login",
                }
            )

        result = self._rpc(
            "user.login", {"username": username, "password": password}, use_auth=False
        )
        return json.dumps(result)

    # ------------------------------------------------------------------
    # Hosts
    # ------------------------------------------------------------------

    def zabbix_get_hosts(
        self,
        filter_host: Optional[str] = None,
        hostids: Optional[str] = None,
        groupids: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Retrieve Zabbix hosts. Returns host details including hostid, host name, and status.

        :param filter_host: Optional hostname to filter by (exact match).
        :param hostids: Optional comma-separated list of host IDs to retrieve.
        :param groupids: Optional comma-separated list of host group IDs to filter by.
        :param limit: Maximum number of hosts to return (default 50).
        """
        params: dict = {"output": "extend", "limit": limit}
        if filter_host:
            params["filter"] = {"host": [filter_host]}
        if hostids:
            params["hostids"] = [h.strip() for h in hostids.split(",")]
        if groupids:
            params["groupids"] = [g.strip() for g in groupids.split(",")]

        return json.dumps(self._rpc("host.get", params))

    def zabbix_create_host(
        self,
        hostname: str,
        visible_name: Optional[str] = None,
        group_ids: str = "",
        ip_address: str = "127.0.0.1",
        dns: str = "",
        port: int = 10050,
        use_ip: bool = True,
    ) -> str:
        """
        Create a new host in Zabbix.

        :param hostname: Technical hostname (unique identifier).
        :param visible_name: Optional display name shown in the Zabbix UI.
        :param group_ids: Comma-separated list of host group IDs the host belongs to (required by Zabbix).
        :param ip_address: IP address for the default Zabbix agent interface.
        :param dns: DNS name for the interface (used when use_ip is False).
        :param port: Agent port number (default 10050).
        :param use_ip: If True, use IP address for the interface; otherwise use DNS.
        """
        if not group_ids:
            return json.dumps({"success": False, "error": "group_ids is required"})

        groups = [{"groupid": g.strip()} for g in group_ids.split(",")]
        interfaces = [
            {
                "type": 1,  # Zabbix agent
                "main": 1,
                "useip": 1 if use_ip else 0,
                "ip": ip_address,
                "dns": dns,
                "port": str(port),
            }
        ]
        params: dict = {
            "host": hostname,
            "groups": groups,
            "interfaces": interfaces,
        }
        if visible_name:
            params["name"] = visible_name

        return json.dumps(self._rpc("host.create", params))

    def zabbix_update_host(
        self,
        hostid: str,
        status: Optional[int] = None,
        visible_name: Optional[str] = None,
    ) -> str:
        """
        Update an existing Zabbix host.

        :param hostid: The ID of the host to update.
        :param status: Host status — 0 for monitored, 1 for unmonitored.
        :param visible_name: New visible name for the host.
        """
        params: dict = {"hostid": hostid}
        if status is not None:
            params["status"] = status
        if visible_name:
            params["name"] = visible_name

        return json.dumps(self._rpc("host.update", params))

    def zabbix_delete_host(self, hostids: str) -> str:
        """
        Delete one or more hosts from Zabbix.

        :param hostids: Comma-separated list of host IDs to delete.
        """
        ids = [h.strip() for h in hostids.split(",") if h.strip()]
        if not ids:
            return json.dumps({"success": False, "error": "hostids must not be empty"})

        return json.dumps(self._rpc("host.delete", ids))

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------

    def zabbix_get_items(
        self,
        hostids: Optional[str] = None,
        search_key: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Retrieve monitoring items from Zabbix hosts.

        :param hostids: Optional comma-separated list of host IDs to filter items by.
        :param search_key: Optional substring to search for within item keys.
        :param limit: Maximum number of items to return (default 50).
        """
        params: dict = {"output": "extend", "limit": limit}
        if hostids:
            params["hostids"] = [h.strip() for h in hostids.split(",")]
        if search_key:
            params["search"] = {"key_": search_key}

        return json.dumps(self._rpc("item.get", params))

    def zabbix_create_item(
        self,
        hostid: str,
        name: str,
        key: str,
        item_type: int = 0,
        value_type: int = 3,
        delay: str = "30s",
        interface_id: str = "0",
    ) -> str:
        """
        Create a new monitoring item on a Zabbix host.

        :param hostid: ID of the host to add the item to.
        :param name: Display name of the item.
        :param key: Item key (e.g. 'agent.ping', 'system.cpu.load').
        :param item_type: Zabbix item type — 0=Zabbix agent, 2=Zabbix trapper, 7=Zabbix agent (active).
        :param value_type: Data type — 0=float, 1=char, 2=log, 3=unsigned int, 4=text.
        :param delay: Collection interval (e.g. '30s', '1m').
        :param interface_id: Interface ID to use (0 for default).
        """
        params = {
            "hostid": hostid,
            "name": name,
            "key_": key,
            "type": item_type,
            "value_type": value_type,
            "delay": delay,
            "interfaceid": interface_id,
        }
        return json.dumps(self._rpc("item.create", params))

    def zabbix_update_item(
        self, itemid: str, delay: Optional[str] = None, status: Optional[int] = None
    ) -> str:
        """
        Update an existing Zabbix item.

        :param itemid: ID of the item to update.
        :param delay: New collection interval (e.g. '60s').
        :param status: Item status — 0 for enabled, 1 for disabled.
        """
        params: dict = {"itemid": itemid}
        if delay:
            params["delay"] = delay
        if status is not None:
            params["status"] = status

        return json.dumps(self._rpc("item.update", params))

    # ------------------------------------------------------------------
    # Triggers
    # ------------------------------------------------------------------

    def zabbix_get_triggers(
        self,
        hostids: Optional[str] = None,
        only_true: bool = False,
        min_severity: int = 0,
        limit: int = 50,
    ) -> str:
        """
        Retrieve Zabbix triggers (alert conditions).

        :param hostids: Optional comma-separated list of host IDs to filter by.
        :param only_true: If True, return only triggers currently in PROBLEM state.
        :param min_severity: Minimum severity level — 0=not classified, 1=info, 2=warning, 3=average, 4=high, 5=disaster.
        :param limit: Maximum number of triggers to return (default 50).
        """
        params: dict = {
            "output": "extend",
            "limit": limit,
            "min_severity": min_severity,
        }
        if hostids:
            params["hostids"] = [h.strip() for h in hostids.split(",")]
        if only_true:
            params["only_true"] = 1

        return json.dumps(self._rpc("trigger.get", params))

    def zabbix_create_trigger(
        self,
        description: str,
        expression: str,
        priority: int = 2,
        recovery_expression: str = "",
    ) -> str:
        """
        Create a new Zabbix trigger.

        :param description: Human-readable trigger name.
        :param expression: Zabbix trigger expression (e.g. 'last(/myhost/agent.ping)=0').
        :param priority: Severity — 0=not classified, 1=info, 2=warning, 3=average, 4=high, 5=disaster.
        :param recovery_expression: Optional recovery expression for problem resolution.
        """
        params: dict = {
            "description": description,
            "expression": expression,
            "priority": priority,
        }
        if recovery_expression:
            params["recovery_mode"] = 1
            params["recovery_expression"] = recovery_expression

        return json.dumps(self._rpc("trigger.create", params))

    def zabbix_update_trigger(
        self,
        triggerid: str,
        status: Optional[int] = None,
        priority: Optional[int] = None,
    ) -> str:
        """
        Update an existing Zabbix trigger.

        :param triggerid: ID of the trigger to update.
        :param status: Trigger status — 0 for enabled, 1 for disabled.
        :param priority: New severity level (0–5).
        """
        params: dict = {"triggerid": triggerid}
        if status is not None:
            params["status"] = status
        if priority is not None:
            params["priority"] = priority

        return json.dumps(self._rpc("trigger.update", params))

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def zabbix_get_events(
        self,
        hostids: Optional[str] = None,
        triggerids: Optional[str] = None,
        min_severity: int = 0,
        limit: int = 50,
        time_from: Optional[int] = None,
        time_till: Optional[int] = None,
    ) -> str:
        """
        Retrieve Zabbix events (problems and recoveries).

        :param hostids: Optional comma-separated list of host IDs to filter by.
        :param triggerids: Optional comma-separated list of trigger IDs to filter by.
        :param min_severity: Minimum severity level (0–5).
        :param limit: Maximum number of events to return (default 50).
        :param time_from: Optional start time as a Unix timestamp.
        :param time_till: Optional end time as a Unix timestamp.
        """
        params: dict = {
            "output": "extend",
            "source": 0,  # trigger events
            "object": 0,
            "sortfield": ["clock", "eventid"],
            "sortorder": "DESC",
            "limit": limit,
            "min_severity": min_severity,
        }
        if hostids:
            params["hostids"] = [h.strip() for h in hostids.split(",")]
        if triggerids:
            params["objectids"] = [t.strip() for t in triggerids.split(",")]
        if time_from is not None:
            params["time_from"] = time_from
        if time_till is not None:
            params["time_till"] = time_till

        return json.dumps(self._rpc("event.get", params))
