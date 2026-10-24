"""Functional tests for pages as the ASA Stats app sees them.

Chrome sends the app's user-agent token, as the Capacitor WebView does.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest

APP_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 16; Pixel 8; wv) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Version/4.0 Chrome/141.0.0.0 Mobile Safari/537.36 "
    "ASAStatsApp/1.1.0 (android)"
)


def _store_links(browser):
    return browser.find_elements(
        By.CSS_SELECTOR, "a[href*='apps.apple.com'], a[href*='play.google.com']"
    )


def _app_js_requested(browser):
    return browser.execute_script(
        "return performance.getEntriesByType('resource')"
        ".some(function (entry) { return entry.name.indexOf('/js/app.js') !== -1; });"
    )


class AppClientPagesTest(FunctionalTest):
    """A page loaded with the app's token is in app mode."""

    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def test_app_page_is_marked_in_app(self):
        self.browser.get(self.server_url + reverse("faq"))
        html = self.browser.find_element(By.TAG_NAME, "html")

        self.assertIn("in-app", html.get_attribute("class").split())
        self.assertEqual(html.get_attribute("data-app-platform"), "android")
        viewport = self.browser.find_element(By.CSS_SELECTOR, "meta[name=viewport]")
        self.assertIn("viewport-fit=cover", viewport.get_attribute("content"))

    def test_app_page_hides_the_store_links(self):
        self.browser.get(self.server_url + reverse("faq"))

        self.assertEqual(_store_links(self.browser), [])

    def test_app_page_loads_app_js(self):
        self.browser.get(self.server_url + reverse("faq"))

        self.assertTrue(_app_js_requested(self.browser))
        self.assertTrue(self.browser.execute_script("return window.ASAStatsApp.isApp;"))


class BrowserPagesTest(FunctionalTest):
    """The same page without the token is the plain website."""

    def test_browser_page_is_not_in_app(self):
        self.browser.get(self.server_url + reverse("faq"))
        html = self.browser.find_element(By.TAG_NAME, "html")

        self.assertNotIn("in-app", (html.get_attribute("class") or "").split())
        self.assertIsNone(html.get_attribute("data-app-platform"))
        viewport = self.browser.find_element(By.CSS_SELECTOR, "meta[name=viewport]")
        self.assertNotIn("viewport-fit", viewport.get_attribute("content"))

    def test_browser_page_shows_the_store_links(self):
        self.browser.get(self.server_url + reverse("faq"))

        self.assertEqual(len(_store_links(self.browser)), 2)

    def test_browser_page_does_not_load_app_js(self):
        self.browser.get(self.server_url + reverse("faq"))

        self.assertFalse(_app_js_requested(self.browser))
        self.assertIsNone(self.browser.execute_script("return window.ASAStatsApp;"))
