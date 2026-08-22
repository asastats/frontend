"""Functional tests for profile_api.html.

Written because of the specific way this page failed. Both clipboard controls
carried `cursor-pointer` and no `.copy`, so they said "click me" and did
nothing at all -- `site.js` binds `copyToClipboard` to `.copy`. Three other
templates had it right, which is exactly why it went unnoticed: the control
looks identical everywhere and only this copy of it was inert. Nothing in the
suite noticed either, because a template test sees a span with the classes the
template asked for and has no opinion about whether anything is listening.

So the assertion here is that pressing the control **copies the token**, taken
from `navigator.clipboard` rather than from the markup.

The second half of the contract is positional and just as easy to break
silently: `copyToClipboard` copies `$(this).prev()`, the element *immediately
before* the control. Wrapping the token in a div "for layout" leaves the
control bound, leaves it looking right, and copies the wrong thing -- or
nothing. That is asserted by comparing what was copied against the token on
screen, not by looking at where the elements sit.

The page is gated: `CanAccessApiMixin` requires Asastatser, so a fixture below
that tier lands on the subscriptions page instead. That is the reason
`test_profile_pages.py` leaves this page out of its sweep.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

from .base import FunctionalTest

ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]

#: Replaces the real clipboard, which headless Chrome will not write to without
#: a permission grant. Installed before the click so the control's own code
#: path is the one under test -- `site.js` skips the copy entirely when
#: `navigator.clipboard` is absent, and a test that let it be absent would pass
#: against a control bound to nothing.
CLIPBOARD_STUB = """
window.__copied = [];
Object.defineProperty(navigator, 'clipboard', {
  configurable: true,
  value: {
    writeText: function (text) {
      window.__copied.push(text);
      return Promise.resolve();
    }
  }
});
"""


class ApiTokenPageTest(FunctionalTest):
    """The token page for a reader whose tier reaches it."""

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier(
            "apiuser@example.com", permission=ASASTATSER
        )

    def _open(self, refresh=False):
        """Open the page, optionally asking for a fresh token pair."""
        url = self.server_url + reverse("profile_api")
        self.state = self.visit(url + ("?refresh=yes" if refresh else ""))

    def test_a_reader_below_the_tier_does_not_reach_the_page(self):
        """Gated, and the redirect is to something to buy rather than a 403."""
        self.create_cookie_and_go_to_index_page_tier("nofunds@example.com", permission=0)

        self.browser.get(self.server_url + reverse("profile_api"))

        self.assertNotIn("/profile/api/", self.browser.current_url)

    def test_a_reader_with_no_tokens_is_told_what_to_do(self):
        """An empty state that says something, rather than an empty area."""
        self._open()

        self.assertIn("You have no tokens yet", self.browser.page_source)
        obtain = self.find_elem_by_id("id_obtain")
        self.assertEqual("obtain token pair", obtain.text.strip().lower())

    def test_obtaining_a_pair_shows_both_tokens(self):
        self._open(refresh=True)

        self.assertNotEqual(
            self.state["title"],
            "Internal server error",
            f"the API page raised{self.state['why']}",
        )
        labels = [
            p.text.strip()
            for p in self.browser.find_elements(By.CSS_SELECTOR, "main p")
        ]
        self.assertIn("Refresh token", labels)
        self.assertIn("Access token", labels)

        tokens = self.browser.find_elements(By.CSS_SELECTOR, "main code[aria-labelledby]")
        self.assertEqual(2, len(tokens), "the page did not show two tokens")
        for token in tokens:
            with self.subTest(token=token.get_attribute("aria-labelledby")):
                # A JWT, not an empty box: the page is worthless if the value
                # it exists to hand over is blank.
                self.assertGreater(len(token.text.strip()), 20)

    def test_the_copy_control_copies_the_token_beside_it(self):
        """The control that was dead, exercised.

        Both halves at once: that something is bound to it at all, and that
        what it copies is the token immediately before it rather than whatever
        happens to be nearby.
        """
        self._open(refresh=True)
        self.browser.execute_script(CLIPBOARD_STUB)

        controls = self.browser.find_elements(By.CSS_SELECTOR, "main button.copy")
        self.assertEqual(2, len(controls), "the token rows carry no copy controls")

        expected = []
        for control in controls:
            token = self.browser.execute_script(
                "return arguments[0].previousElementSibling.textContent.trim();",
                control,
            )
            expected.append(token)
            control.click()

        copied = self.browser.execute_script("return window.__copied;")
        self.assertEqual(
            expected,
            copied,
            "the copy controls did not put the tokens on the clipboard",
        )
        # And what they copied is what the reader can see, which is what makes
        # the positional contract testable without asserting on the markup.
        self.assertEqual(
            [
                code.text.strip()
                for code in self.browser.find_elements(
                    By.CSS_SELECTOR, "main code[aria-labelledby]"
                )
            ],
            copied,
        )

    def test_each_copy_control_says_what_it_copies(self):
        """Two identical clipboard glyphs, one after the other.

        Without a label they are announced as "button, button", and the reader
        has to guess which token they are about to put on the clipboard.
        """
        self._open(refresh=True)

        labels = [
            control.get_attribute("aria-label")
            for control in self.browser.find_elements(By.CSS_SELECTOR, "main button.copy")
        ]
        self.assertEqual(["Copy refresh token", "Copy access token"], labels)

    def test_each_token_is_announced_with_its_name(self):
        """`aria-labelledby` ties the value to the caption above it.

        A 200-character string announced on its own says nothing about which of
        the two tokens it is.
        """
        self._open(refresh=True)

        for token in self.browser.find_elements(
            By.CSS_SELECTOR, "main code[aria-labelledby]"
        ):
            caption_id = token.get_attribute("aria-labelledby")
            with self.subTest(token=caption_id):
                caption = self.browser.find_element(By.ID, caption_id)
                self.assertIn("token", caption.text.strip().lower())

    def test_obtaining_a_new_pair_warns_that_it_invalidates_the_old(self):
        """The one destructive thing on the page, said before it happens."""
        self._open(refresh=True)

        self.assertIn("invalidates the tokens above", self.browser.page_source)
        obtain = self.find_elem_by_id("id_obtain")
        self.assertEqual("obtain a new pair", obtain.text.strip().lower())
