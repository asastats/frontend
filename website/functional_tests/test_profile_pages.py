"""Functional tests for the signed-in pages, which share one shape.

Both shells are a single centred column now. ``base_profile.html`` adds a
segmented sub-nav across the top; ``base_home.html`` -- home and the three
bundle-name forms -- does not, because those pages are not a section a reader
moves between.

There used to be a rail here, and these tests used to pin the source order that
kept a phone from meeting the navigation before the content. It was produced by
Materialize's ``push-m10``/``pull-m2`` pair. The profile section left it on
2026-08-22 and home followed the same day, so there is no source-order question
left to get backwards: one column stacks correctly by construction. What is
pinned instead is that no ``aside`` comes back.

Page-specific flows live in their own modules -- test_profile_edit,
test_profile_authorize, test_profile_account, test_home_page -- most of which
predate this one.
"""

from datetime import UTC, datetime, timedelta
from unittest import mock

from django.urls import reverse
from selenium.webdriver.common.by import By

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

from .base import FunctionalTest

#: What the chain would answer for a reader holding one tier. A real tier name,
#: because `_format_tier_name_as_link` looks the name up in
#: SUBSCRIPTION_PERMISSIONS and raises for one that is not there, and a future
#: expiry so the page renders "expires in N days" rather than "EXPIRED".
SUBSCRIPTION_FROM_CHAIN = {
    "Asastatser": int((datetime.now(UTC) + timedelta(days=30)).timestamp())
}

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

#: Every signed-in page, both shells. Nothing here should grow a rail again.
SINGLE_COLUMN_PAGES = SIGNED_IN_PAGES


class SignedInShellTest(FunctionalTest):
    """The shared shape: a header, breadcrumbs, and one centred column."""

    def setUp(self):
        super().setUp()
        # `/profile/` reads the reader's subscriptions off mainnet: for an
        # authorized profile, ProfileView.get_context_data asks the permission
        # provider, which asks a node once per subscription tier. Live network,
        # inside a page render, in a browser test.
        #
        # It went unnoticed because the node address comes from the
        # permission-dApp's own environment, which a developer machine has and
        # CI does not -- so here it built a client with address None and the
        # page became a 500, and locally it "passed" by calling Algonode four
        # times per visit. Same shape as the `.env` values pinned in
        # config/settings/automated_tests.py, and the same fix: decide the
        # answer here rather than inherit it.
        #
        # The provider and its formatters still run; only the node call is
        # replaced. The live-server thread shares this process, so the patch
        # reaches the view.
        chain = mock.patch(
            "core.permission_providers.permissiondapp."
            "fetch_subscriptions_for_address",
            return_value=SUBSCRIPTION_FROM_CHAIN,
        )
        chain.start()
        self.addCleanup(chain.stop)

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
                # Scoped to <main>. Both shells make the page title an h1 now,
                # but the sweep still accepts either level: the footer carries
                # an h2 per group on every page, so an unscoped selector would
                # pass on a page with no header at all.
                self.assertTrue(
                    self.browser.find_elements(By.CSS_SELECTOR, "main h1, main h2"),
                    f"{name} lost its page header{state['why']}",
                )
                self.assertTrue(
                    self.browser.find_elements(By.CSS_SELECTOR, "nav"),
                    f"{name} lost its navigation{state['why']}",
                )

    def test_no_signed_in_page_has_a_rail(self):
        """One centred column everywhere, so the stacking question cannot arise.

        This replaced a test asserting the opposite -- that home *had* a rail
        and that the main column preceded it in source, so a phone met the
        content first. Both shells dropped the rail on 2026-08-22, for the same
        reason: on these pages it held breadcrumbs and a box repeating the
        reader's email, and three-quarters of the column was empty.

        Pinned as an absence because a rail is the kind of thing that comes back
        when somebody needs somewhere to put a new control.
        """
        for name in SINGLE_COLUMN_PAGES:
            with self.subTest(page=name):
                self.browser.get(self.server_url + reverse(name))
                self.assertFalse(
                    self.browser.find_elements(By.TAG_NAME, "aside"),
                    f"{name} grew a rail again",
                )

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


class LiveRefreshSettingTest(FunctionalTest):
    """The real-time refresh opt-in, both sides of its gate.

    A browser test because both sides are markup decisions: whether the reader
    gets a control they can use, or one they can see and a way to buy it. A unit
    test on the view cannot tell those apart.
    """

    def _open(self, permission, who="reader"):
        """Open the settings page as a reader of `permission`.

        **A reader per test**, because one of these saves the preference and a
        shared account would carry it into the next test - which is how the
        "off until asked for" test came to fail only when the class ran
        together, and pass on its own.
        """
        self.create_cookie_and_go_to_index_page_tier(
            f"liverefresh-{who}@example.com", permission=permission
        )
        self.browser.get(self.server_url + reverse("profile_settings"))

    def test_a_subscriber_gets_a_checkbox_they_can_use(self):
        self._open(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], "enabled")

        section = self.browser.find_element(By.ID, "id-section-liverefresh")
        checkbox = section.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')

        assert checkbox.is_enabled()
        assert section.find_elements(By.ID, "id_save_liverefresh")

    def test_it_is_off_until_the_subscriber_asks_for_it(self):
        """The tier buys the choice, not the behaviour: a page that updates
        itself is not what everyone wants."""
        self._open(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], "default")

        section = self.browser.find_element(By.ID, "id-section-liverefresh")
        checkbox = section.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')

        assert not checkbox.is_selected()

    def test_below_the_tier_the_control_works_and_names_the_daily_limit(self):
        """**This asserted a disabled control until the allowance existed.**

        The house pattern for a setting somebody cannot have is to show it
        disabled, name the tier and link out. Below Asastatser nobody could have
        this at all, so that was right. They can now - 15 minutes a day with no
        tier, 30 with Intro - and an allowance a reader cannot switch on is not
        an allowance, so the control is live.

        The upgrade prompt did not disappear, it moved to where it means
        something: the number, beside the checkbox they are ticking, rather than
        a page that quietly stops on them twenty minutes later.
        """
        self._open(SUBSCRIPTION_TIER_PERMISSIONS["Intro"], "limited")

        section = self.browser.find_element(By.ID, "id-section-liverefresh")
        checkbox = section.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]')
        link = section.find_element(By.TAG_NAME, "a")

        assert checkbox.is_enabled()
        assert "30 minutes" in section.text
        assert reverse("subscriptions") in link.get_attribute("href")

    def test_a_subscriber_is_told_nothing_about_limits(self):
        """They have none, and a prompt to subscribe would be addressed to
        somebody who already has."""
        self._open(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], "unlimited")

        section = self.browser.find_element(By.ID, "id-section-liverefresh")

        assert "minutes" not in section.text

    def test_a_free_reader_is_told_the_address_must_be_connected(self):
        """**The restriction that decides whether the feature works for them.**

        A free reader may spend their allowance only on an address they have
        proved they control, so a page opened on somebody else's address simply
        will not refresh. Finding that out by watching a page fail to update is
        the worst way to learn it; the tier that carries the restriction is the
        tier that gets the sentence.
        """
        self._open(0, "freetold")

        section = self.browser.find_element(By.ID, "id-section-liverefresh")

        assert "connected to your account" in section.text

    def test_a_paying_reader_is_not_told_about_connected_addresses(self):
        """It does not apply to them, and a restriction described to somebody it
        does not restrict reads as one that does.

        Covers both paying shapes in one assertion each: Intro has an allowance
        but no `linked_only`, Asastatser has no allowance at all - and the
        template keys on `linked_only` rather than on "has terms", so the two
        cannot be collapsed.
        """
        for permission, who in (
            (SUBSCRIPTION_TIER_PERMISSIONS["Intro"], "introfree"),
            (SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], "paidfree"),
        ):
            self._open(permission, who)

            section = self.browser.find_element(By.ID, "id-section-liverefresh")

            assert "connected to your account" not in section.text

    def test_the_saved_preference_comes_back_checked(self):
        """A setting that does not survive a reload is a setting nobody trusts."""
        self._open(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], "saver")
        section = self.browser.find_element(By.ID, "id-section-liverefresh")
        section.find_element(By.CSS_SELECTOR, 'input[type="checkbox"]').click()
        section.find_element(By.ID, "id_save_liverefresh").click()

        self.wait_until(
            lambda: self.browser.find_element(
                By.CSS_SELECTOR, "#id-section-liverefresh input[type='checkbox']"
            ).is_selected()
        )

        self.browser.get(self.server_url + reverse("profile_settings"))
        assert self.browser.find_element(
            By.CSS_SELECTOR, "#id-section-liverefresh input[type='checkbox']"
        ).is_selected()


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
