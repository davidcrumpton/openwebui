import json
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def tools(load_tool):
    return load_tool("zabbix/zabbix.py")


@pytest.fixture
def mock_requests_post():
    with patch('requests.post') as mock_post:
        yield mock_post


class TestZabbixTools:
    def test_loads(self, tools):
        assert tools is not None

    def test_zabbix_login_success(self, tools, mock_requests_post):
        # Mock successful login response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": "abc123def456",
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        # Set up environment variables for login
        tools.valves.ZABBIX_USER = "testuser"
        tools.valves.ZABBIX_PASSWORD = "testpass"
        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_login()
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_login_failure_no_credentials(self, tools):
        # Test login with no credentials set
        tools.valves.ZABBIX_USER = ""
        tools.valves.ZABBIX_PASSWORD = ""
        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_login()
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == False

    def test_zabbix_get_hosts(self, tools, mock_requests_post):
        # Mock successful hosts response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": [
                {
                    "hostid": "10101",
                    "host": "test host",
                    "name": "Test Host"
                }
            ],
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_get_hosts()
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_create_host(self, tools, mock_requests_post):
        # Mock successful host creation response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "hostids": ["10201"]
            },
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_create_host(
            hostname="testhost",
            group_ids="1,2"
        )
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_create_host_no_groupids(self, tools):
        # Test creating host without group_ids (should fail)
        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_create_host(
            hostname="testhost",
            group_ids=""
        )
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == False

    def test_zabbix_update_host(self, tools, mock_requests_post):
        # Mock successful host update response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {},
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_update_host(
            hostid="10201",
            status=0
        )
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_delete_host(self, tools, mock_requests_post):
        # Mock successful host deletion response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "hostids": ["10201"]
            },
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_delete_host("10201")
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_get_items(self, tools, mock_requests_post):
        # Mock successful items response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": [
                {
                    "itemid": "20101",
                    "name": "Test Item",
                    "key_": "test.key"
                }
            ],
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_get_items()
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_create_item(self, tools, mock_requests_post):
        # Mock successful item creation response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "itemids": ["20101"]
            },
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_create_item(
            hostid="10201",
            name="Test Item",
            key="test.key"
        )
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_update_item(self, tools, mock_requests_post):
        # Mock successful item update response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {},
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_update_item(
            itemid="20101",
            delay="60s"
        )
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_get_triggers(self, tools, mock_requests_post):
        # Mock successful triggers response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": [
                {
                    "triggerid": "30101",
                    "description": "Test Trigger",
                    "priority": 2
                }
            ],
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_get_triggers()
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_create_trigger(self, tools, mock_requests_post):
        # Mock successful trigger creation response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "triggerids": ["30101"]
            },
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_create_trigger(
            description="Test Trigger",
            expression="{host:agent.ping.nodata(10m)}=1"
        )
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_update_trigger(self, tools, mock_requests_post):
        # Mock successful trigger update response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {},
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_update_trigger(
            triggerid="30101",
            priority=3
        )
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True

    def test_zabbix_get_events(self, tools, mock_requests_post):
        # Mock successful events response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": [
                {
                    "eventid": "40101",
                    "source": 0,
                    "object": 0
                }
            ],
            "id": 1
        }
        mock_response.status_code = 200
        mock_requests_post.return_value = mock_response

        tools.valves.ZABBIX_API_URL = "http://zabbix.example.com/api_jsonrpc.php"

        result = tools.zabbix_get_events()
        assert result is not None
        parsed_result = json.loads(result)
        assert parsed_result["success"] == True
