import pytest


@pytest.fixture
def tools(load_tool):
    return load_tool("link-fetch-tool/link-fetch-tool.py")


class TestLinkFetchTool:
    def test_loads(self, tools):
        assert tools is not None

    async def test_fetch_page_content(self, tools, kwargs_for):
        kwargs = kwargs_for(tools, "fetch_page_content", url="https://www.example.com")
        result = await tools.fetch_page_content(**kwargs)
        assert result is not None
