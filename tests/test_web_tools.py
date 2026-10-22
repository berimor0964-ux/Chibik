import pytest

from app.ai.web_tools import (
    BrowserManager,
    BrowserOpenTool,
    BrowserReadTool,
    BrowserTypeTool,
    BrowserClickTool,
    EdgeSearchTool,
    WebSearchTool,
    _validate_public_url,
)


def test_web_search_tool_has_openai_schema():
    tool = WebSearchTool().to_openai_tool()
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "web_search"
    assert "query" in tool["function"]["parameters"]["required"]


def test_edge_search_tool_has_openai_schema():
    tool = EdgeSearchTool().to_openai_tool()
    assert tool["function"]["name"] == "edge_search"
    assert tool["function"]["parameters"]["properties"]["engine"]["enum"]


@pytest.mark.parametrize(
    "url",
    [
        "file:///C:/Windows/win.ini",
        "ftp://example.com/file",
        "http://localhost",
        "http://127.0.0.1",
        "http://192.168.1.1",
        "http://user:password@example.com",
    ],
)
def test_private_or_unsupported_urls_are_rejected(url):
    with pytest.raises(ValueError):
        _validate_public_url(url)


def test_browser_tools_share_browser_instance():
    browser = BrowserManager()
    assert BrowserOpenTool(browser).browser is browser
    assert BrowserReadTool(browser).browser is browser
    assert BrowserTypeTool(browser).browser is browser
    assert BrowserClickTool(browser).browser is browser
    browser.close()


def test_empty_search_query_is_rejected():
    with pytest.raises(ValueError):
        WebSearchTool().execute(query="   ")


def test_invalid_edge_engine_is_rejected_before_launching_browser():
    with pytest.raises(ValueError):
        EdgeSearchTool().execute(query="desktop pet", engine="unknown")
