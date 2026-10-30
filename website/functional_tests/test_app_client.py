"""Functional tests for pages as the ASA Stats app sees them.

Chrome sends the app's user-agent token, as the Capacitor WebView does.
"""

from django.test import override_settings
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
        # app.js is a loader: the global appears once its chunk has run.
        self.wait_until(
            lambda: self.browser.execute_script("return !!window.ASAStatsApp;")
        )
        self.assertTrue(self.browser.execute_script("return window.ASAStatsApp.isApp;"))
        self.assertEqual(
            self.browser.execute_script("return typeof window.ASAStatsApp.download;"),
            "function",
        )


    def test_app_page_keeps_app_lock_hidden_without_the_plugin(self):
        # Chrome has no native bridge, as an app build from before the plugin.
        self.browser.get(self.server_url + reverse("faq"))
        self.wait_until(
            lambda: self.browser.execute_script("return !!window.ASAStatsApp;")
        )

        entry = self.browser.find_element(By.CSS_SELECTOR, "[data-app-lock-settings]")
        self.assertFalse(entry.is_displayed())


class BrowserPagesTest(FunctionalTest):
    """The same page without the token is the plain website."""

    def test_browser_page_is_not_in_app(self):
        self.browser.get(self.server_url + reverse("faq"))
        html = self.browser.find_element(By.TAG_NAME, "html")

        self.assertNotIn("in-app", (html.get_attribute("class") or "").split())
        self.assertIsNone(html.get_attribute("data-app-platform"))
        viewport = self.browser.find_element(By.CSS_SELECTOR, "meta[name=viewport]")
        self.assertNotIn("viewport-fit", viewport.get_attribute("content"))

    def test_browser_page_has_no_app_lock_entry(self):
        self.browser.get(self.server_url + reverse("faq"))

        self.assertEqual(
            self.browser.find_elements(By.CSS_SELECTOR, "[data-app-lock-settings]"), []
        )

    def test_browser_page_shows_the_store_links(self):
        self.browser.get(self.server_url + reverse("faq"))

        self.assertEqual(len(_store_links(self.browser)), 2)

    def test_browser_page_does_not_load_app_js(self):
        self.browser.get(self.server_url + reverse("faq"))

        self.assertFalse(_app_js_requested(self.browser))
        self.assertIsNone(self.browser.execute_script("return window.ASAStatsApp;"))


PURCHASE_LINKS = (
    "a[href*='/subscriptions/'], a[href*='subtopia.io'], "
    "a[href*='app.pact.fi'], a[href*='app.tinyman.org']"
)


class AppPurchaseLinksTest(FunctionalTest):
    """No page the app shows links towards buying or upgrading (F10)."""

    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def _assert_no_purchase_links(self, names):
        for name in names:
            with self.subTest(page=name):
                self.browser.get(self.server_url + reverse(name))
                hrefs = [
                    link.get_attribute("href")
                    for link in self.browser.find_elements(By.CSS_SELECTOR, PURCHASE_LINKS)
                ]
                self.assertEqual(hrefs, [])

    def test_signed_out_pages_have_no_purchase_links(self):
        self._assert_no_purchase_links(
            ["index", "faq", "subscriptions", "about", "features", "tokenomics"]
        )

    def test_signed_in_pages_have_no_purchase_links(self):
        self.create_cookie_and_go_to_index_page_tier("app-purchase@example.com")
        self._assert_no_purchase_links(
            ["home", "profile_settings", "profile_appearance", "profile_account"]
        )

    def test_subscriptions_page_shows_plans_without_buying(self):
        self.browser.get(self.server_url + reverse("subscriptions"))
        body = self.browser.find_element(By.TAG_NAME, "body").text

        self.assertIn("Subscription Models", body)
        self.assertNotIn("How to Subscribe", body)
        self.assertNotIn("ASASTATS / Month", body)


@override_settings(
    APP_HIDDEN_WIDGETS={"android": frozenset({"historic"}), "ios": frozenset()}
)
class AppHiddenWidgetsTest(FunctionalTest):
    """A widget switched off for the app's platform is not served to it (F11)."""

    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def test_hidden_widget_is_page_not_found(self):
        self.create_cookie_and_go_to_index_page_tier("app-hidden@example.com")
        self.browser.get(self.server_url + reverse("historic", args=["A" * 58]))

        self.assertEqual(self.browser.title, "Page not found")
