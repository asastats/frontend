"""Functional tests for the app's system-browser sign-in (F4).

The provider dance itself is not driven (it leaves the test server): a
session that has just signed in stands in for it, as allauth leaves one.
"""

from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from django.utils import timezone
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.views_appauth import PROVIDERS, SESSION_KEY, challenge_for

from .base import COOKIE_SEED_URL, FunctionalTest
from .test_app_client import APP_USER_AGENT

VERIFIER = "v" * 43

#: The redeem form app.js builds (`wallet/src/app/signIn.ts:redeem`).
REDEEM_SCRIPT = """
var form = document.createElement("form");
form.method = "POST";
form.action = arguments[0];
var fields = {ticket: arguments[1], verifier: arguments[2],
              csrfmiddlewaretoken: document.cookie.match(/csrftoken=([^;]+)/)[1]};
Object.keys(fields).forEach(function (name) {
  var input = document.createElement("input");
  input.type = "hidden"; input.name = name; input.value = fields[name];
  form.appendChild(input);
});
document.body.appendChild(form);
form.submit();
"""


class AppSignInButtonsTest(FunctionalTest):
    """In the app, every social button names its provider for app.js."""

    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def test_app_login_page_buttons_carry_data_app_signin(self):
        self.browser.get(self.server_url + reverse("account_login"))

        providers = {
            button.get_attribute("data-app-signin")
            for button in self.browser.find_elements(By.CSS_SELECTOR, "[data-app-signin]")
        }
        expected = set(PROVIDERS) - {"apple"}  # Apple's keys are unset in tests.
        self.assertEqual(providers, expected)
        self.assertEqual(
            self.browser.execute_script("return typeof window.ASAStatsApp.signIn;"),
            "function",
        )


class AppSignInFlowTest(FunctionalTest):
    """complete → return → redeem, as the sheet and the WebView do it."""

    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def _signed_in_browser_session(self, next_url):
        cookie = self.create_session_cookie(username="sheet@example.com", password="pw")
        from django.contrib.sessions.backends.db import SessionStore

        session = SessionStore(session_key=cookie["value"])
        session[SESSION_KEY] = {
            "challenge": challenge_for(VERIFIER),
            "next": next_url,
            "started": timezone.now().timestamp(),
        }
        session.save()
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(cookie)

    def test_app_signin_ticket_signs_the_webview_in(self):
        self._signed_in_browser_session(next_url="/profile/")

        # The sheet: complete hands over a ticket and leaves the browser signed out.
        self.browser.get(self.server_url + reverse("app_auth_complete"))
        WebDriverWait(self.browser, 10).until(EC.url_contains("/app/auth/return/"))
        ticket = parse_qs(urlparse(self.browser.current_url).query)["ticket"][0]
        message = self.browser.find_element(By.ID, "id_app_auth_message")
        self.assertEqual(message.get_attribute("data-kind"), "return")
        self.assertNotIn(ticket, self.browser.page_source)

        # The WebView: a page with a CSRF cookie, then the redeem form.
        self.browser.get(self.server_url + reverse("account_login"))
        self.browser.execute_script(
            REDEEM_SCRIPT, reverse("app_auth_redeem"), ticket, VERIFIER
        )
        WebDriverWait(self.browser, 10).until(EC.url_contains("/profile/"))
        self.assertEqual(urlparse(self.browser.current_url).path, "/profile/")

    def test_app_signin_second_redeem_is_refused(self):
        self._signed_in_browser_session(next_url="/profile/")
        self.browser.get(self.server_url + reverse("app_auth_complete"))
        WebDriverWait(self.browser, 10).until(EC.url_contains("/app/auth/return/"))
        ticket = parse_qs(urlparse(self.browser.current_url).query)["ticket"][0]
        self.browser.get(self.server_url + reverse("account_login"))
        self.browser.execute_script(
            REDEEM_SCRIPT, reverse("app_auth_redeem"), ticket, VERIFIER
        )
        WebDriverWait(self.browser, 10).until(EC.url_contains("/profile/"))
        self.browser.delete_all_cookies()

        self.browser.get(self.server_url + reverse("account_login"))
        self.browser.execute_script(
            REDEEM_SCRIPT, reverse("app_auth_redeem"), ticket, VERIFIER
        )
        message = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, "id_app_auth_message"))
        )
        self.assertEqual(message.get_attribute("data-kind"), "expired")
