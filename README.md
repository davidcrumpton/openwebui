# Open WebUI stuff

## Tools

Custom tools I use for Open WebUI.  They are meant to be placed in the `tools` directory of the Open WebUI installation.

## This Repo

This repo allows you to use the VS Code debugging and testing tools to test the tools in the `tools` directory.

### Testing

To test the tools, use `pytest`.  Use `pytest --cov` to run the tests with coverage.  Use `pytest --cov-report=term` to run the tests with coverage and print the report to the terminal.

```bash
export OPENWEBUI_TEST_HOME_ASSISTANT_URL="http://localhost:8123"
export OPENWEBUI_TEST_HOME_ASSISTANT_TOKEN="dummy_token"
pytest tests/test_home_assistant_tool.py
```

### Home Assistant Tool

This tool is meant to be used for Home Assistant.  It uses the Home Assistant API to get information about the home assistant instance.  The HA instance is located at `http://localhost:8123`.  It uses a long lived token for authentication.  You can get the token by going to the Home Assistant UI and selecting "My Profile" and then "Long Lived Access Tokens".

Use the `get_entities` function to get a list of all entities in the home assistant instance.  Use the `get_entity` function to get information about a specific entity.  Use the `call_service` function to call a service in the home assistant instance.

### Zabbix Tool

This tool is meant to be used for Zabbix.  It uses the Zabbix API to get information about the Zabbix instance.  The Zabbix instance is located at `http://localhost:8080`.  It uses a username and password for authentication.  You can get the username and password by going to the Zabbix UI and selecting "Administration" and then "Users".

Use the `get_hosts` function to get a list of all hosts in the Zabbix instance.  Use the `get_items` function to get information about a specific item.  Use the `get_triggers` function to get information about a specific trigger.  Use the `get_events` function to get information about a specific event.

### Wiki Tool

This tool is meant to be used for Wiki.js.  It uses the Wiki.js API to get information about the Wiki.js instance.  The Wiki.js instance is located at `http://localhost:8080`.  It uses a username and password for authentication.  You can get the username and password by going to the Wiki.js UI and selecting "Administration" and then "Users".

Use the `get_pages` function to get a list of all pages in the Wiki.js instance.  Use the `get_page` function to get information about a specific page.  Use the `get_page_content` function to get the content of a specific page.  Use the `get_page_tree` function to get the tree structure of the Wiki.js instance.  Use the `search_wiki` function to search the Wiki.js instance.

### Work Space Daemon

This tool is used to manage my work space.  It uses a MCP server to communicate with the work space.  The MCP server is located at `http://localhost:8080`.  It uses a username and password for authentication.  You can get the username and password by going to the MCP Host Engine UI and selecting "Administration" and then "Users".  Use the `list_files` function to list the files in a directory.  Use the `get_file_content` function to get the content of a file.  Use the `create_file` function to create a file.  Use the `update_file` function to update a file.  Use the `delete_file` function to delete a file.  Use the `list_directories` function to list the directories in a directory.  Use the `create_directory` function to create a directory.  Use the `delete_directory` function to delete a directory.  Use the `list_workspace_processes` function to list the processes running in the work space.  Use the `get_workspace_process` function to get information about a specific process.  Use the `kill_workspace_process` function to kill a process.  Use the `list_workspace_containers` function to list the containers running in the work space.  Use the `get_workspace_container` function to get information about a specific container.  Use the `kill_workspace_container` function to kill a container.  Use the `list_workspace_services` function to list the services running in the work space.  Use the `get_workspace_service` function to get information about a specific service.  Use the `kill_workspace_service` function to kill a service.  

### Zabbix

This tool is used to get information about Zabbix.  It uses the Zabbix API to get information about the Zabbix instance.  The Zabbix instance is located at `http://localhost:8080`.  It uses a username and password for authentication.  You can get the username and password by going to the Zabbix UI and selecting "Administration" and then "Users".  Use the `get_hosts` function to get a list of all hosts in the Zabbix instance.  Use the `get_items` function to get information about a specific item.  Use the `get_triggers` function to get information about a specific trigger.  Use the `get_events` function to get information about a specific event.  Use the `get_graphs` function to get information about a specific graph.  Use the `get_screens` function to get information about a specific screen.  Use the `get_maps` function to get information about a specific map.  Use the `get_dashboards` function to get information about a specific dashboard.  Use the `get_dashboards` function to get information about a specific dashboard.  

### web search

This tool calls duck duck go to search the web.  Use the `search` function to search the web and returns the page stripped of HTML tags.

### Link Fetch Tool

This tool does a GET request to retrieve a link and returns the data stripped of HTML tags.

### GitLab Tool

This tool is used to manage my GitLab repos.  It uses the GitLab API to get information about my GitLab instance.  The GitLab instance is located at `http://localhost:8080`.  It uses a username and password for authentication.  You can get the username and password by going to the GitLab UI and selecting "Administration" and then "Users".  Use the `list_projects` function to list all projects.  Use the `get_project` function to get information about a specific project.  Use the `get_project_content` function to get the content of a specific file in a project.  Use the `get_project_tree` function to get the tree structure of a project.  Use the `search_gitlab` function to search the GitLab instance.
