"""Offline unit tests for the optional browser integration.

These tests must never launch a browser or perform a real web search.
"""
import pytest

from app.ai.web_tools import (
    BrowserManager,
    BrowserOpenTool,
    BrowserReadTool,
    BrowserTypeTool,
    BrowserClickTool,
)


def test_browser_wrappers_share_the_same_manager():
    manager = BrowserManager()
    assert BrowserOpenTool(manager).browser is manager
    assert BrowserReadTool(manager).browser is manager
    assert BrowserTypeTool(manager).browser is manager
    assert BrowserClickTool(manager).browser is manager
    manager.close()


def test_browser_manager_is_lazy():
    manager = BrowserManager()
    assert manager._playwright is None
    assert manager._context is None
    assert manager._page is None
    manager.close()
