"""Functional tests for the Dust Sweep widget's page.

Three ways in, all covered here: the standalone tool at
``/widgets/dustsweep/<address>``, the entry on a single address's page, and the
entry on a bundle page - which is the one that has to choose between several of
the reader's own accounts, and the one that got it wrong.

**Nothing here signs anything.** The wallet bridge (``window.asastatsSwap``)
ships with the wallet bundle and is absent in a bare browser, which is exactly
the state a reader is in before connecting - and the state these assertions
describe. What the page must do without a wallet is render, name its endpoint,
and refuse to offer a sweep of an address the reader does not own.

**Why the shell carries so little.** Every decision a sweep makes - what is
dust, what may be forfeited, which group comes next - is made in the engine
against live chain state. If a threshold or an asset list or a creator address
appeared in this markup it would be a value a reader could edit into something
the server then acted on, so the tests below assert their *absence* as firmly
as they assert the plan URL's presence.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By

from walletauth.models import LinkedAddress

from .base import FunctionalTest

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


class DustSweepPageTest(FunctionalTest):
    """Load the sweep shell as a reader who owns the address."""

    def _link_address(self, email="dustsweep@example.com"):
        """Log a user in and connect ADDRESS to them, which is what gates a sweep."""
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=100
        )
        user = get_user_model().objects.get(username=email)
        LinkedAddress.objects.create(
            profile=user.profile,
            address=ADDRESS,
            canonical_address=ADDRESS,
            chain="algorand",
            auth_method="algorand_wallet",
            is_primary=True,
            login_enabled=True,
        )
        user.profile.address = ADDRESS
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def _open_page(self):
        self.browser.get(f"{self.server_url}/widgets/dustsweep/{ADDRESS}")
        return self.find_elem_by_id("id-dustsweep")

    def test_the_sweep_page_loads_rather_than_404ing(self):
        """Mounted, which is what makes the URL resolve at all.

        Asserted through the reader's eyes - a heading they can see - rather
        than on a status code, because a Django view can return 200 and render
        an error shell. The asastats widget was discovered by manifest but
        never mounted, and nothing failed loudly; this is the test that would
        have caught the same mistake here.
        """
        self._link_address()
        self._open_page()

        assert "Dust Sweep" in self.find_elem_by_class("dustsweep-page-title").text
        assert "Dust Sweep" in self.browser.title

    def test_the_shell_carries_the_plan_url_the_controller_needs(self):
        """The one endpoint is the whole configuration.

        `dustsweep.js` reads it off the shell; a template that stopped emitting
        it would leave the page looking correct and unable to plan anything.
        """
        self._link_address()
        shell = self._open_page()

        assert shell.get_attribute("data-widget") == "dustsweep"
        assert shell.get_attribute("data-plan-url").endswith("/plan")

    def test_no_sweep_parameter_reaches_the_browser(self):
        """The engine decides; the browser renders.

        A threshold or a creator address in this markup would be a decision a
        reader could edit. Their absence is what keeps the forfeit - the one
        part of a sweep that can take something - entirely server-side.
        """
        self._link_address()
        shell = self._open_page()

        for attribute in (
            "data-threshold",
            "data-creator",
            "data-forfeit",
            "data-assets",
            "data-fee-bps",
        ):
            assert shell.get_attribute(attribute) is None, attribute

    def test_the_owned_address_is_offered_with_its_own_button(self):
        """One row per linked address, each opening the modal for that address.

        A sweep acts on one account at a time - the groups it builds are signed
        by a single holder - so the address travels on the button rather than
        being inferred from the page.
        """
        self._link_address()
        self._open_page()

        rows = self.find_elems_by_css("#id-dustsweep-addresses li[data-address]")
        assert len(rows) == 1
        assert rows[0].get_attribute("data-address") == ADDRESS

        button = rows[0].find_element(By.CSS_SELECTOR, ".id-dustsweep-open")
        assert button.get_attribute("data-address") == ADDRESS

    def test_the_modal_is_closed_until_the_reader_opens_it(self):
        """A native `<dialog>`: closed means not rendered, not merely hidden."""
        self._link_address()
        self._open_page()

        modal = self.find_elem_by_id("dustsweep-modal")
        assert modal.get_attribute("open") is None
        assert not modal.is_displayed()

    def test_opening_the_modal_shows_the_sweep_interface(self):
        """The whole point of this pass: there is an interface to show.

        Asserted through what a reader sees - the modal opens, names the
        address it will sweep, and offers the controls - rather than on
        internal state. Planning itself needs a live engine, which a functional
        test does not have, so the CTA is still in its reading state here.
        """
        self._link_address()
        self._open_page()

        self.find_elem_by_css(".id-dustsweep-open").click()
        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)

        assert modal.is_displayed()
        assert "Dust Sweep" in self.find_elem_by_css(".dustsweep-title").text
        # the address is named, shortened, so a reader can tell which one
        assert ADDRESS[:6] in self.find_elem_by_css(".id-dustsweep-address-tag").text
        assert self.find_elem_by_css(".id-dustsweep-cta").is_displayed()

    def test_the_modal_closes_again(self):
        """Escape and the close button both have to work, or it is a trap."""
        self._link_address()
        self._open_page()

        self.find_elem_by_css(".id-dustsweep-open").click()
        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)

        self.find_elem_by_css(".id-dustsweep-close").click()
        self.wait_until(lambda: modal.get_attribute("open") is None)

    def test_the_threshold_control_offers_presets_and_a_custom_field(self):
        """The only input the reader has, and the engine clamps it anyway.

        Low presets because the unsafe direction is upward: a mistyped
        threshold must not be able to reach a balance somebody meant to keep.
        """
        self._link_address()
        self._open_page()
        self.find_elem_by_css(".id-dustsweep-open").click()

        presets = self.find_elems_by_css(".id-dustsweep-threshold-preset")
        assert [one.get_attribute("data-threshold") for one in presets] == [
            "0.1",
            "1",
            "5",
        ]
        assert max(float(one.get_attribute("data-threshold")) for one in presets) <= 10

    def test_the_filter_tabs_default_to_what_will_be_swept(self):
        """A reader opening a sweep wants to see what is about to happen.

        "Everything" exists so a holding the sweep left alone is still
        visible - without it there is no way to tell "kept deliberately" from
        "missed".
        """
        self._link_address()
        self._open_page()
        self.find_elem_by_css(".id-dustsweep-open").click()

        tabs = self.find_elems_by_css("[data-dustsweep-filter]")
        selected = [one for one in tabs if one.get_attribute("aria-selected") == "true"]
        assert len(selected) == 1
        assert selected[0].get_attribute("data-dustsweep-filter") == "sweeping"

    def test_the_page_explains_what_it_recovers_before_anything_is_signed(self):
        """Most of what a sweep returns is minimum balance, not tokens.

        A reader who thinks they are selling dust will judge the result by the
        tokens and conclude it did nothing. The page says so up front, and that
        sentence is part of the product rather than decoration.
        """
        self._link_address()
        self._open_page()

        intro = self.find_elem_by_class("dustsweep-intro").text
        assert "0.1" in intro
        assert "minimum balance" in intro

    def test_the_page_names_no_framework_classes(self):
        """The widget emits semantic hooks; the host paints them.

        Naming a DaisyUI class here would couple the submodule to a framework
        version that changes underneath it, and - because the widget stylesheet
        loads *after* the host's - would override that class for the whole
        page, host chrome included.
        """
        self._link_address()
        shell = self._open_page()

        markup = shell.get_attribute("outerHTML")
        for framework in ('class="btn', '"card"', '"stack"', '"tooltip'):
            assert framework not in markup, framework

        # nor the swap widget's own vocabulary: a sweep is not a swap, and
        # borrowing `swap-*` would tie it to rules changed for swap reasons
        assert "swap-" not in markup

    def test_the_page_loads_without_javascript_errors(self):
        """`dustsweep.js` runs here with no wallet bridge beside it.

        The bridge ships with the wallet bundle and is absent in a bare
        browser. The controller has to tolerate that rather than throwing,
        because it is every reader's state before connecting.
        """
        self._link_address()
        self.record_javascript_errors()
        self._open_page()

        assert self.javascript_errors() == []


class DustSweepPageUnlinkedTest(FunctionalTest):
    """A reader who does not own the address is told, not offered a sweep."""

    def test_an_unlinked_reader_is_told_to_connect_rather_than_shown_a_panel(self):
        """Ownership gates the panel, and the message has to be visible.

        Stronger here than on a swap page: a sweep reads a whole account and
        returns a group that closes its holdings out. The locked notice and the
        address list are mutually exclusive in the template, and asserting both
        directions is what stops a future edit rendering the panel for someone
        who does not own the address.
        """
        session_cookie = self.create_session_cookie(
            username="dustsweep-unlinked@example.com",
            password="top_secret",
            permission=100,
        )
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        self.browser.get(f"{self.server_url}/widgets/dustsweep/{ADDRESS}")

        locked = self.find_elem_by_id("id-dustsweep-locked")
        assert locked.is_displayed()
        assert "Connect the wallet" in locked.text

        # `find_elems_by_css` waits for presence *before* returning the list,
        # so it can never express absence - asked for something that is not
        # there it times out rather than returning []. The driver's own
        # `find_elements` returns an empty list immediately, which is the only
        # way to assert a thing is missing.
        assert (
            self.browser.find_elements(
                By.CSS_SELECTOR, "#id-dustsweep-addresses li[data-address]"
            )
            == []
        )


class DustSweepAddressPageEntryTest(FunctionalTest):
    """The entry point: reaching the sweep from the address page.

    The address page is ``cache_page``'d across users, so this arrives through
    the same non-cached htmx partial the swap entry uses. That is not an
    optimisation - rendering "is this address yours?" into the shared page
    would serve one reader's answer to everyone who came after.
    """

    def _link_address(self, email="dustsweep-entry@example.com"):
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=100
        )
        user = get_user_model().objects.get(username=email)
        LinkedAddress.objects.create(
            profile=user.profile,
            address=ADDRESS,
            canonical_address=ADDRESS,
            chain="algorand",
            auth_method="algorand_wallet",
            is_primary=True,
            login_enabled=True,
        )
        user.profile.address = ADDRESS
        user.profile.preferred_router = "folks"
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def test_a_linked_reader_is_offered_the_sweep_on_the_address_page(self):
        """The whole point of an entry point: it can be found without a URL.

        Waited for rather than asserted immediately, because it arrives by
        htmx after the page has loaded - the address page is the heaviest on
        the site and the partial lands last.
        """
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")

        button = self.find_elem_by_css(".id-dustsweep-open")
        assert button.is_displayed()
        assert "Sweep" in button.text
        assert button.get_attribute("data-address") == ADDRESS

    def test_the_sweep_opens_from_the_address_page(self):
        """It is wired there too, not merely rendered.

        The controller binds on its own rather than waiting for the wallet
        bridge, so this works for a reader who has not connected - which is
        every reader, the first time.
        """
        self._link_address()
        self.browser.get(f"{self.server_url}/{ADDRESS}")

        self.find_elem_by_css(".id-dustsweep-open").click()
        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)
        assert modal.is_displayed()

    def test_an_unlinked_reader_is_offered_nothing(self):
        """The gate is ownership, and it is applied server-side.

        Not hidden with CSS: the markup must not be there at all, because a
        button that appears for everyone and works for nobody is worse than no
        button.
        """
        session_cookie = self.create_session_cookie(
            username="dustsweep-nolink@example.com",
            password="top_secret",
            permission=100,
        )
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        self.browser.get(f"{self.server_url}/{ADDRESS}")

        # let the htmx partial land before concluding it rendered nothing
        self.find_elem_by_id("id-swap-entry-container")
        assert self.browser.find_elements(By.CSS_SELECTOR, ".id-dustsweep-open") == []


class DustSweepBundlePageEntryTest(FunctionalTest):
    """Reaching the sweep from a *bundle* page, which is where it went wrong.

    A bundle page shows several addresses consolidated, and a sweep is signed
    by one holder's key. The entry used to pick whichever of the reader's own
    addresses sorted first and say nothing about it, so a reader whose wallet
    was connected to the other one got a group that account cannot sign.
    """

    OTHER = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
    THIRD = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"
    BUNDLE = "540A5D8CEC896E073F9170AF0A962503E69147CF"

    def _link(self, addresses, primary, email="dustsweep-bundle@example.com"):
        """Connect every address in `addresses`, making `primary` the primary."""
        session_cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=100
        )
        user = get_user_model().objects.get(username=email)
        for one in addresses:
            LinkedAddress.objects.create(
                profile=user.profile,
                address=one,
                canonical_address=one,
                chain="algorand",
                auth_method="algorand_wallet",
                is_primary=one == primary,
                login_enabled=True,
            )
        user.profile.address = primary
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def _open_bundle(self, addresses):
        with mock.patch(
            "core.views.check_bundle_addresses", return_value=" ".join(addresses)
        ):
            self.browser.get(f"{self.server_url}/{self.BUNDLE}")
            # inside the patch, because the htmx partial is a second request
            # and it is the one that resolves the bundle
            self.find_elem_by_id("id-swap-entry-container")
            return self.wait_until(
                lambda: self.browser.find_elements(
                    By.CSS_SELECTOR, ".id-dustsweep-open"
                )
            )

    def test_every_owned_address_in_the_bundle_gets_its_own_button(self):
        """The reader chooses, because only they know what is connected.

        Three addresses on the page, two of them theirs: two buttons, and the
        third is not offered at all.
        """
        self._link([ADDRESS, self.OTHER], primary=ADDRESS)
        buttons = self._open_bundle([ADDRESS, self.OTHER, self.THIRD])

        offered = sorted(one.get_attribute("data-address") for one in buttons)
        assert offered == sorted([ADDRESS, self.OTHER])

    def test_each_button_names_the_address_it_will_sweep(self):
        """Two identical buttons would be a coin toss with somebody's tokens."""
        self._link([ADDRESS, self.OTHER], primary=ADDRESS)
        buttons = self._open_bundle([ADDRESS, self.OTHER])

        for button in buttons:
            address = button.get_attribute("data-address")
            assert address[:6] in button.text
            assert address[-4:] in button.text

    def test_the_modal_opens_on_the_address_its_button_named(self):
        """The bug, asserted end to end.

        Clicking the second button must sweep the second address - not the one
        the server happened to pick as a default.
        """
        self._link([ADDRESS, self.OTHER], primary=ADDRESS)
        buttons = self._open_bundle([ADDRESS, self.OTHER])
        chosen = next(
            one for one in buttons if one.get_attribute("data-address") == self.OTHER
        )
        chosen.click()

        modal = self.find_elem_by_id("dustsweep-modal")
        self.wait_until(lambda: modal.get_attribute("open") is not None)
        tag = self.find_elem_by_css(".id-dustsweep-address-tag").text
        assert self.OTHER[:6] in tag
        assert self.OTHER[-4:] in tag

    def test_a_reader_who_owns_none_of_the_bundle_is_offered_nothing(self):
        """"If the connected address isn't in the bundle, no action is possible."."""
        self._link([self.THIRD], primary=self.THIRD)
        with mock.patch(
            "core.views.check_bundle_addresses",
            return_value=f"{ADDRESS} {self.OTHER}",
        ):
            self.browser.get(f"{self.server_url}/{self.BUNDLE}")
            self.find_elem_by_id("id-swap-entry-container")
            assert (
                self.browser.find_elements(By.CSS_SELECTOR, ".id-dustsweep-open") == []
            )
