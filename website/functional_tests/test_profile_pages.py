"""Functional tests for the signed-in pages, which now use two shells.

The profile section moved to base_profile.html: one centred column with a
segmented sub-nav across the top. base_home.html still carries the older
arrangement -- a main column with a narrow left rail for breadcrumbs -- and
home and the bundle-name pages are still on it.

The rail assertions below therefore belong to base_home, not to every
signed-in page. The rail was produced by Materialize's ``push-m10``/``pull-m2``
pair, which put it left on wide screens while leaving the main column first in
source; that arrangement is still pinned here, because getting it backwards
would hand a phone the navigation before the content.

Page-specific flows live in their own modules -- test_profile_edit,
test_profile_authorize, test_profile_account -- which predate this one.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest

#: Every page a signed-in viewer can reach without a tier, whichever shell it
#: uses. profile_api is absent on purpose: CanAccessApiMixin gates it on the
#: subscription tier, so it needs a fixture of its own rather than a place in a
#: broad sweep.
SIGNED_IN_PAGES = [
    "home",
    "profile",
    "profile_account",
    "profile_settings",
    "profile_addresses",
    "deactivate_profile",
]

#: The pages still on base_home.html, which is where the rail lives.
RAILED_PAGES = ["home"]


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
                # Scoped to <main>, and accepting either level. The two shells
                # disagree -- base_profile makes the page title an h1, base_home
                # an h2 -- and the footer carries an h2 per group on every page,
                # so an unscoped `h2` would pass on a page with no header at all.
                self.assertTrue(
                    self.browser.find_elements(By.CSS_SELECTOR, "main h1, main h2"),
                    f"{name} lost its page header{state['why']}",
                )
                self.assertTrue(
                    self.browser.find_elements(By.CSS_SELECTOR, "nav"),
                    f"{name} lost its navigation{state['why']}",
                )

    def test_the_main_column_precedes_the_rail_in_source_order(self):
        """A phone stacks in source order, so the content has to come first.

        On wide screens CSS moves the rail to the left; that is a visual
        reordering only, which is the whole reason source order matters here.

        Asserted against base_home, which is the shell that still has a rail.
        The profile section moved to base_profile and has none -- one centred
        column stacks correctly by construction, with nothing to get backwards.
        """
        for name in RAILED_PAGES:
            with self.subTest(page=name):
                self.browser.get(self.server_url + reverse(name))
                order = self.browser.execute_script(
                    "var rail = document.querySelector('aside');"
                    "if (!rail) return null;"
                    "return Array.from(rail.parentElement.children).map("
                    "  function (c) { return c.tagName; });"
                )
                self.assertIsNotNone(order, f"{name} lost the left rail")
                self.assertLess(order.index("DIV"), order.index("ASIDE"))

    def test_the_profile_section_has_no_rail_to_get_backwards(self):
        """base_profile is one column, so the stacking question does not arise.

        Pinned because the rail's removal is the point of that redesign: if an
        aside reappears here, the section has drifted back to the old shell.
        """
        self.browser.get(self.server_url + reverse("profile"))

        self.assertFalse(self.browser.find_elements(By.TAG_NAME, "aside"))

    def test_breadcrumbs_lead_back_up_the_hierarchy(self):
        """Found by their landmark, not by the box they sit in.

        They used to live in the rail, so this looked for an `aside`; the
        profile section has no rail now. What makes them breadcrumbs is the
        labelled navigation landmark, which is the same in either shell and is
        also how a screen reader finds them.
        """
        self.browser.get(self.server_url + reverse("profile_account"))

        crumbs = self.browser.find_element(
            By.CSS_SELECTOR, 'nav[aria-label="Breadcrumb"]'
        )
        hrefs = [a.get_attribute("href") for a in crumbs.find_elements(By.TAG_NAME, "a")]

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
