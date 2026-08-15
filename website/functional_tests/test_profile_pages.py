"""Functional tests for the signed-in pages built on base_home.html.

These share a shell: a page header, a main column, and a narrow left rail
carrying breadcrumbs. The rail used to be produced by Materialize's
``push-m10``/``pull-m2`` pair, which put it left on wide screens while leaving
the main column first in source; the tests below pin that arrangement, because
getting it backwards would hand a phone the navigation before the content.

Page-specific flows live in their own modules -- test_profile_edit,
test_profile_authorize, test_profile_account -- which predate this one.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest

#: Pages on base_home.html reachable by any signed-in viewer. profile_api is
#: absent on purpose: CanAccessApiMixin gates it on the subscription tier, so
#: it needs a fixture of its own rather than a place in a broad sweep.
SIGNED_IN_PAGES = [
    "home",
    "profile",
    "profile_account",
    "profile_settings",
    "profile_addresses",
    "deactivate_profile",
]


class SignedInShellTest(FunctionalTest):
    """The shared shell: every page gets a header, a main column and a rail."""

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier(
            "shell@example.com", permission=100
        )

    def test_every_signed_in_page_renders_its_header_and_breadcrumbs(self):
        for name in SIGNED_IN_PAGES:
            with self.subTest(page=name):
                state = self.visit(self.server_url + reverse(name))
                self.assertNotEqual(
                    state["title"],
                    "Internal server error",
                    f"{name} raised in the view{state['why']}",
                )
                self.assertTrue(
                    self.browser.find_elements(By.CSS_SELECTOR, "h2"),
                    f"{name} lost its page header{state['why']}",
                )
                self.assertTrue(
                    self.browser.find_elements(By.TAG_NAME, "aside"),
                    f"{name} lost the left rail{state['why']}",
                )

    def test_the_main_column_precedes_the_rail_in_source_order(self):
        """A phone stacks in source order, so the content has to come first.

        On wide screens CSS moves the rail to the left; that is a visual
        reordering only, which is the whole reason source order matters here.
        """
        self.browser.get(self.server_url + reverse("profile"))
        order = self.browser.execute_script(
            "var grid = document.querySelector('aside').parentElement;"
            "return Array.from(grid.children).map(function (c) { return c.tagName; });"
        )
        self.assertEqual(order.index("DIV") < order.index("ASIDE"), True)

    def test_breadcrumbs_lead_back_up_the_hierarchy(self):
        self.browser.get(self.server_url + reverse("profile_account"))
        rail = self.browser.find_element(By.TAG_NAME, "aside")
        hrefs = [a.get_attribute("href") for a in rail.find_elements(By.TAG_NAME, "a")]
        self.assertTrue(any(reverse("home") in h for h in hrefs))
        self.assertTrue(any(reverse("profile") in h for h in hrefs))


class LinkedAddressesPageTest(FunctionalTest):
    """profile_addresses.html: one native <details> per connected address."""

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier("rows@example.com", permission=100)
        self.browser.get(self.server_url + reverse("profile_addresses"))

    def test_the_wallet_manager_container_is_present_for_the_package(self):
        """frontend/wallet binds to these ids; the conversion must not move
        them, or the step-up flow silently stops working."""
        self.assertTrue(self.browser.find_elements(By.ID, "connected-addresses"))
        self.assertTrue(self.browser.find_elements(By.ID, "connected-addresses-list"))

    def test_rows_are_native_disclosures_that_need_no_javascript(self):
        """These were a Materialize collapsible, re-initialised after every
        htmx swap. They are <details> now, so a freshly swapped list works on
        arrival -- and the re-init listener could be deleted."""
        rows = self.browser.find_elements(By.CSS_SELECTOR, ".connected-address-row")
        # The {% empty %} branch renders a row too, and it carries no <details>
        # because there is nothing to disclose.
        rows = [r for r in rows if r.get_attribute("id")]
        for row in rows:
            with self.subTest(row=row.get_attribute("id")):
                self.assertTrue(row.find_elements(By.TAG_NAME, "details"))
                self.assertTrue(row.find_elements(By.TAG_NAME, "summary"))

    def test_an_empty_list_says_so(self):
        # The fixture user has no linked addresses.
        self.assertIn("No addresses yet", self.browser.page_source)


class SettingsPageTest(FunctionalTest):
    """profile_settings.html, whose selects are rendered by Django forms."""

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier(
            "prefs@example.com", permission=100
        )
        self.browser.get(self.server_url + reverse("profile_settings"))

    def test_the_preference_selects_render(self):
        selects = self.browser.find_elements(By.TAG_NAME, "select")
        self.assertTrue(selects)
        # `browser-default` existed only to opt out of Materialize's select
        # styling; on this stylesheet it would mean nothing, so it is gone.
        for select in selects:
            with self.subTest(select=select.get_attribute("id")):
                self.assertNotIn("browser-default", select.get_attribute("class") or "")

    def test_each_select_is_labelled(self):
        for select in self.browser.find_elements(By.TAG_NAME, "select"):
            field_id = select.get_attribute("id")
            if not field_id:
                continue
            with self.subTest(select=field_id):
                self.assertTrue(
                    self.browser.find_elements(
                        By.CSS_SELECTOR, f'label[for="{field_id}"]'
                    ),
                    f"{field_id} has no label",
                )
