import pytest

@pytest.fixture
def tools(load_tool):
    return load_tool("link-fetch-tool/link-fetch-tool.py")


class TestLinkFetchTool:
    def test_loads(self, tools):
        assert tools is not None

    def test_fetch_success(self, tools, kwargs_for):
        kwargs = kwargs_for(tools, "fetch", url="https://www.example.com")
        result = tools.fetch(**kwargs)
        assert result.get("status") == "success"
        assert result.get("content") is not None
        assert result.get("final_url") is not None

    def test_fetch_invalid_url(self, tools):
        """Test fetch with invalid URL"""
        result = tools.fetch(url="")
        assert result.get("error") == "Invalid URL"

    def test_fetch_with_html_stripping(self, tools, kwargs_for):
        """Test fetch with HTML stripping enabled (default)"""
        kwargs = kwargs_for(tools, "fetch", url="https://www.example.com")
        result = tools.fetch(**kwargs, strip_html=True)
        assert result.get("status") == "success"
        assert result.get("content_type") == "text"
        assert isinstance(result.get("content"), str)
        assert len(result.get("content")) > 0

    def test_fetch_without_html_stripping(self, tools, kwargs_for):
        """Test fetch with HTML stripping disabled"""
        kwargs = kwargs_for(tools, "fetch", url="https://www.example.com")
        result = tools.fetch(**kwargs, strip_html=False)
        assert result.get("status") == "success"
        assert result.get("content_type") == "html"
        assert isinstance(result.get("content"), str)
        assert len(result.get("content")) > 0

    def test_fetch_time_measurement(self, tools, kwargs_for):
        """Test that fetch_time_seconds is measured correctly"""
        kwargs = kwargs_for(tools, "fetch", url="https://www.example.com")
        result = tools.fetch(**kwargs)
        assert result.get("status") == "success"
        assert "fetch_time_seconds" in result
        assert isinstance(result.get("fetch_time_seconds"), (int, float))
        assert result.get("fetch_time_seconds") >= 0

