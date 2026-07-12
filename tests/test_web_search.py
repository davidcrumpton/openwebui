import json
import pytest


@pytest.fixture
def tools(load_tool):
    return load_tool("web-search/ddg.py")


class TestWebSearchTools:
    def test_loads(self, tools):
        assert tools is not None

    def test_search_returns_results(self, tools):
        """
        Live search against DuckDuckGo — no env vars required.
        Set a breakpoint here to step through the HTTP fetch and result parsing.
        """
        raw = tools.search("OpenWebUI python tools", max_results=3)

        # The method always returns a JSON string.
        result = json.loads(raw)

        print("\n--- DuckDuckGo search result ---")
        print(json.dumps(result, indent=2))

        assert "query" in result
        assert "count" in result
        assert "results" in result
        assert result["count"] >= 0  # may be 0 if DDG blocks the request

        for item in result["results"]:
            assert "title" in item
            assert "url" in item
            assert "snippet" in item

    def test_search_empty_query(self, tools):
        """Error path: empty query should return an error key, not raise."""
        raw = tools.search("")
        result = json.loads(raw)
        assert "error" in result

    def test_search_max_results_clamped(self, tools):
        """max_results is clamped to [1, 10] internally."""
        raw = tools.search("Python", max_results=100)
        result = json.loads(raw)
        # Should not raise; result count must be <= 10
        assert result.get("count", 0) <= 10
