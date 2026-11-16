import unittest
from unittest.mock import patch

from app.ai import web_tools


class OptionalBrowserDependencyTests(unittest.TestCase):
    def test_browser_manager_can_be_created_without_starting_playwright(self):
        manager = web_tools.BrowserManager()
        self.assertIsNone(manager._playwright)
        self.assertIsNone(manager._context)
        self.assertIsNone(manager._page)

    def test_missing_playwright_reports_actionable_error_only_when_used(self):
        manager = web_tools.BrowserManager()
        with patch.object(web_tools, "sync_playwright", None):
            with self.assertRaisesRegex(RuntimeError, "requirements-browser.txt"):
                manager._ensure_open()


if __name__ == "__main__":
    unittest.main()
