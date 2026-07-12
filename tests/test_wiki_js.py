from tests.conftest import kwargs_for
import pytest


@pytest.fixture
def tools(load_tool):
    return load_tool("wikijs/wikijs.py")

class TestWikiJs:
    def test_loads(self, tools):
        assert tools is not None

    async def test_get_wiki_pages(self, tools, kwargs_for):
        kwargs = kwargs_for(tools, "get_wiki_pages", wiki_url="https://wiki.crumpton.org", username="admin", password="[PASSWORD]") 
        result = await tools.get_wiki_pages(**kwargs)
        assert result is not None
        
    async def test_get_wiki_pages_content(self, tools, kwargs_for):
        kwargs = kwargs_for(tools, "get_wiki_pages_content", wiki_url="https://wiki.crumpton.org", username="admin", password="[PASSWORD]", page_id="1") 
        result = await tools.get_wiki_pages_content(**kwargs)
        assert result is not None
        
    async def test_get_wiki_pages_tree(self, tools, kwargs_for):
        kwargs = kwargs_for(tools, "get_wiki_pages_tree", wiki_url="https://wiki.crumpton.org", username="admin", password="[PASSWORD]") 
        result = await tools.get_wiki_pages_tree(**kwargs)
        assert result is not None
        
    async def test_search_wiki(self, tools, kwargs_for):
        kwargs = kwargs_for(tools, "search_wiki", wiki_url="https://wiki.crumpton.org", username="admin", password="[PASSWORD]", search="test") 
        result = await tools.search_wiki(**kwargs)
        assert result is not None
        
    async def test_get_wiki_page_by_slug(self, tools, kwargs_for):
        kwargs = kwargs_for(tools, "get_wiki_page_by_slug", wiki_url="https://wiki.crumpton.org", username="admin", password="[PASSWORD]", slug="test") 
        result = await tools.get_wiki_page_by_slug(**kwargs)
        assert result is not None

    async def test_loads_empty_creds(self, tools):
        kwargs = kwargs_for(tools, "get_wiki_pages", wiki_url="https://wiki.crumpton.org", username="", password="") 
        result = await tools.get_wiki_pages(**kwargs)
        assert result is not None

    async def test_loads_empty_creds(self, tools):
        kwargs = kwargs_for(tools, "get_wiki_pages", wiki_url="https://wiki.crumpton.org", username="", password="") 
        result = await tools.get_wiki_pages(**kwargs)
        assert result is not None