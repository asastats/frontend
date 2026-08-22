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


class LinkedAddressActionsTest(FunctionalTest):
    """The button hierarchy has to survive an htmx swap.

    Every action on this page was a plain `btn`, so "Remove" -- irreversible,
    and the one thing here that asks for confirmation -- looked exactly like
    "Make primary", and "Add address", the reason most people open the page,
    looked like neither. One primary per view, destructive actions marked, the
    rest quiet.

    What makes it worth a functional test rather than a template one is the
    swap: `profile_addresses_action` re-renders `#address_list` server-side
    after every operation, so the classes are set again by the partial rather
    than surviving in the DOM. A hierarchy that lives only in the full-page
    template disappears the first time a reader presses anything.

    The rows are created directly. Linking one through the wallet flow needs a
    signature from a real wallet, which is not something a functional test can
    produce, and none of it is what is under test here.
    """

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier("rows2@example.com", permission=100)
        self._add_addresses()
        self.browser.get(self.server_url + reverse("profile_addresses"))

    def _add_addresses(self):
        """Give the fixture user a primary and one secondary that can log in."""
        from django.contrib.auth import get_user_model

        from walletauth.models import LinkedAddress

        profile = get_user_model().objects.get(username="rows2@example.com").profile
        for address, primary in (
            ("PRIMARYADDRESS2222222222222222222222222222222222222222AAAA", True),
            ("SECONDADDRESS33333333333333333333333333333333333333333BBBB", False),
        ):
            LinkedAddress.objects.create(
                profile=profile,
                address=address,
                canonical_address=address,
                chain="algorand",
                auth_method="algorand_wallet",
                is_primary=primary,
                login_enabled=True,
            )

    def _row(self, index=1):
        """Return one address row, opened so its controls have geometry."""
        rows = [
            row
            for row in self.browser.find_elements(
                By.CSS_SELECTOR, ".connected-address-row"
            )
            if row.get_attribute("id")
        ]
        row = rows[index]
        self.browser.execute_script(
            "arguments[0].querySelector('details').open = true;", row
        )
        return row

    def _classes(self, row):
        """Return each action's label mapped to its class list."""
        return {
            button.text.strip(): button.get_attribute("class")
            for button in row.find_elements(By.CSS_SELECTOR, ".address-actions button")
        }

    def test_the_primary_row_offers_nothing_to_press(self):
        """It cannot be removed, demoted, or have its login disabled.

        Rendering the controls disabled would be worse: three dead buttons say
        the operations exist and are being refused.
        """
        row = self._row(0)

        self.assertFalse(row.find_elements(By.CSS_SELECTOR, ".address-actions button"))
        self.assertIn("This is your primary address", row.text)

    def test_remove_is_marked_destructive_and_make_primary_is_not(self):
        classes = self._classes(self._row())

        self.assertIn("btn-error", classes["Remove"])
        self.assertNotIn("btn-error", classes["Make primary"])
        # Outline, not filled: findable without being the most inviting thing
        # in the row.
        self.assertIn("btn-outline", classes["Remove"])

    def test_add_address_is_the_only_primary_action_on_the_page(self):
        """One filled button per view, and it is the reason people came."""
        filled = [
            control.text.strip()
            for control in self.browser.find_elements(By.CSS_SELECTOR, "main .btn-primary")
        ]

        self.assertEqual(["Add address"], filled)

    def test_the_hierarchy_comes_back_after_an_htmx_swap(self):
        """The assertion this class exists for.

        "Disable login" is the operation to press: it reduces privilege, so the
        server needs no step-up signature, and it carries no `hx-confirm` to
        interrupt. What comes back is a freshly rendered list.
        """
        row = self._row()
        self.assertIn("Disable login", self._classes(row))

        row.find_element(
            By.XPATH, ".//button[normalize-space()='Disable login']"
        ).click()

        # Waited for in the DOM, not in the rendered text: the swapped-in rows
        # arrive as freshly closed `<details>`, so their controls are present
        # and invisible, and `.text` reports only the summaries. The handle is
        # re-fetched for the same reason it is waited for -- the element the
        # click was made on no longer exists.
        self.wait_until(
            lambda: self.browser.find_elements(
                By.XPATH, "//button[normalize-space()='Enable login']"
            )
        )
        classes = self._classes(self._row())

        self.assertIn("btn-error", classes["Remove"])
        self.assertIn("btn-outline", classes["Make primary"])
        self.assertNotIn("btn-primary", classes["Enable login"])

    def test_removing_an_address_asks_first(self):
        """`hx-confirm` is the real guard; the colour is only a warning.

        Dismissing the dialog has to leave the address alone -- a confirmation
        that fires after the fact is worse than none.
        """
        row = self._row()
        row.find_element(By.XPATH, ".//button[normalize-space()='Remove']").click()

        alert = self.browser.switch_to.alert
        self.assertIn("Remove this address", alert.text)
        alert.dismiss()

        self.assertEqual(
            2,
            len(
                [
                    r
                    for r in self.browser.find_elements(
                        By.CSS_SELECTOR, ".connected-address-row"
                    )
                    if r.get_attribute("id")
                ]
            ),
            "the address was removed by a dialog the reader dismissed",
        )
