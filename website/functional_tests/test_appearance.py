"""Functional tests for the appearance picker in the site header.

The site used to offer one alternative appearance -- a dark/light toggle whose
every rule was hand-written, because Materialize has no dark mode. Themes come
from ``settings.AVAILABLE_THEMES`` now, and the choice is stored client-side
and never sent to the server, so most of what matters here is that the choice
survives a page change.
"""

from django.conf import settings
from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest


class AppearancePickerTest(FunctionalTest):
    """The picker itself: what it offers, and what choosing does."""

    def _open_picker(self, page="disclaimer"):
        self.browser.get(self.server_url + reverse(page))
        # A <details>, so it opens without scripting; open it directly rather
        # than clicking, which keeps the test about the choice, not the widget.
        self.browser.execute_script(
            "document.querySelector('#id-theme-list').closest('details').open = true;"
        )
        return self.browser.find_elements(
            By.CSS_SELECTOR, "#id-theme-list input[name='theme-dropdown']"
        )

    def _stamped_theme(self):
        return self.browser.find_element(By.TAG_NAME, "html").get_attribute(
            "data-theme"
        )

    def test_picker_offers_exactly_the_themes_settings_declares(self):
        """The picker is rendered from settings, so adding a theme is a
        settings change plus an input.css registration -- never a template
        edit. core.tests.test_context_processors keeps those two in step."""
        radios = self._open_picker()
        self.assertEqual(
            [r.get_attribute("value") for r in radios],
            list(settings.AVAILABLE_THEMES),
        )

    def test_no_theme_is_stamped_until_one_is_chosen(self):
        self.browser.get(self.server_url + reverse("disclaimer"))
        # Unstamped means DaisyUI's own default applies -- the `asastats` theme
        # is registered with `default: true`, so the page is still branded.
        self.assertIsNone(self._stamped_theme())

    def test_choosing_a_theme_applies_it_and_survives_a_page_change(self):
        radios = self._open_picker()
        target = next(r for r in radios if r.get_attribute("value") == "abyss")
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            target,
        )
        self.wait_until(lambda: self._stamped_theme() == "abyss")

        # The choice is client-side only, so it has to come back from storage,
        # and early enough that the page never paints the default first.
        self.browser.get(self.server_url + reverse("faq"))
        self.wait_until(lambda: self._stamped_theme() == "abyss")

    def test_the_picker_closes_once_a_theme_is_chosen(self):
        radios = self._open_picker()
        menu = self.browser.find_element(
            By.CSS_SELECTOR, "#id-theme-list"
        ).find_element(By.XPATH, "./ancestor::details")
        self.browser.execute_script(
            "arguments[0].dispatchEvent(new Event('change'));", radios[0]
        )
        self.wait_until(lambda: menu.get_attribute("open") is None)

    def test_the_picker_is_reachable_from_every_page_that_has_the_new_header(self):
        # index deliberately blanks {% block header %} -- it is a bare
        # landing page -- so it has no picker to find.
        for page in ("faq", "subscriptions", "account_login", "disclaimer"):
            with self.subTest(page=page):
                self.browser.get(self.server_url + reverse(page))
                self.assertTrue(self.browser.find_elements(By.ID, "id-theme-list"))
