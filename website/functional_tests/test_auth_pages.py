"""Functional tests for the login and signup pages.

Both extend account/base_auth.html, which carries the segmented Sign up / Log
in control, allauth's own form widgets, and the social provider list. The
login-flow behaviour that follows a successful submit lives in
test_custom_login.py; this module is about the pages themselves.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest


class AuthPagesTest(FunctionalTest):
    """The login and signup pages, which share account/base_auth.html."""

    def _open(self, name):
        self.browser.get(self.server_url + reverse(name))
        return self.browser.find_element(By.CSS_SELECTOR, "form")

    def test_the_current_page_is_marked_on_the_segmented_nav(self):
        """The Sign up / Log in pair was a Materialize `.tabs` widget marked
        with `class="active"` -- purely visual. It is `aria-current="page"`
        now, so the state is announced as well as painted."""
        for name, current in (
            ("account_login", "Log in"),
            ("account_signup", "Sign up"),
        ):
            with self.subTest(page=name):
                self.browser.get(self.server_url + reverse(name))
                marked = self.browser.find_elements(
                    By.CSS_SELECTOR, '[aria-current="page"]'
                )
                self.assertEqual([m.text for m in marked], [current])

    def test_the_other_tab_links_to_the_other_page(self):
        self.browser.get(self.server_url + reverse("account_login"))
        signup = self.browser.find_element(
            By.CSS_SELECTOR, f'nav a[href="{reverse("account_signup")}"]'
        )
        self.assertEqual(signup.text, "Sign up")

    def test_allauth_fields_render_and_are_styled(self):
        """allauth builds these widgets with no classes on them, so they are
        styled through the .auth-form scope. If that scope is ever renamed the
        fields silently lose their styling, which this catches."""
        self._open("account_login")
        scope = self.browser.find_elements(By.CSS_SELECTOR, ".auth-form")
        self.assertEqual(len(scope), 1)
        field = self.find_elem_by_id("id_login")
        self.assertIn("Username or email", field.get_attribute("placeholder"))
        # The scope has to actually contain the widgets for the CSS to apply.
        self.assertTrue(scope[0].find_elements(By.ID, "id_login"))

    def test_signup_asks_for_a_password_twice(self):
        self._open("account_signup")
        for field_id in ("id_email", "id_password1", "id_password2"):
            with self.subTest(field=field_id):
                self.assertTrue(self.browser.find_elements(By.ID, field_id))

    def test_every_social_provider_is_offered(self):
        self._open("account_login")
        for provider, href in (
            ("id_discord", "/accounts/discord/login/"),
            ("id_twitter", "/accounts/twitter_oauth2/login/"),
            ("id_reddit", "/accounts/reddit/login/"),
            ("id_github", "/accounts/github/login/"),
            ("id_google", "/accounts/google/login/"),
        ):
            with self.subTest(provider=provider):
                link = self.find_elem_by_id(provider)
                self.assertIn(href, link.get_attribute("href"))

    def test_login_offers_wallet_sign_in(self):
        """login.html includes the DaisyUI wallet snippet, not the Materialize
        one -- the ids the wallet package binds to have to survive."""
        self._open("account_login")
        self.assertTrue(self.browser.find_elements(By.ID, "wallet-connect"))
        self.assertTrue(self.browser.find_elements(By.ID, "evm-wallet-connect"))

    def test_the_form_still_wraps_the_submit_button(self):
        """base_auth.html opens <form> in a block and closes it at the end, so
        a mis-nested conversion would leave the button outside the form."""
        form = self._open("account_login")
        self.assertTrue(form.find_elements(By.CSS_SELECTOR, "button[type='submit']"))
        self.assertTrue(form.find_elements(By.ID, "id_login"))
