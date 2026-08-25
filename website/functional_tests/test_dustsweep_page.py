"""Functional tests for the Dust Sweep widget's page.

The sweep has no modal and no entry on the address page: it is a standalone
tool at ``/widgets/dustsweep/<address>``, reached deliberately rather than
offered alongside a trade. So this file is the only browser-level coverage the
widget has.

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

    def test_the_owned_address_is_offered_with_a_lazy_panel(self):
        """One `<details>` per linked address, each naming the address it sweeps.

        The panel body is empty until the reader opens it - the controller
        plans on the first `toggle` - so the assertion is that the *seam* is
        present and addressed, not that a plan is rendered. Planning needs a
        live engine, which a functional test does not have.
        """
        self._link_address()
        self._open_page()

        rows = self.find_elems_by_css("#id-dustsweep-addresses li[data-address]")
        assert len(rows) == 1
        assert rows[0].get_attribute("data-address") == ADDRESS

        panel = rows[0].find_element(By.CSS_SELECTOR, ".id-dustsweep-panel")
        assert panel.get_attribute("data-address") == ADDRESS
        assert panel.text.strip() == ""

    def test_opening_the_address_reveals_the_panel_seam(self):
        """A reader can actually open the row: `<details>` is not decorative."""
        self._link_address()
        self._open_page()

        selector = "#id-dustsweep-addresses details.dustsweep-address"
        details = self.find_elem_by_css(selector)
        assert details.get_attribute("open") is None

        details.find_element(By.TAG_NAME, "summary").click()
        self.wait_until(
            lambda: self.find_elem_by_css(selector).get_attribute("open") is not None
        )

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
        for framework in ('class="btn', '"card"', '"stack"', '"badge', '"tooltip'):
            assert framework not in markup, framework

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
