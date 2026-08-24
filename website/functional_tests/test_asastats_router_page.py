"""Functional tests for the ASA Stats smart router's own swap page.

The modal on the address page is covered by ``test_swap_widget.py``. This is
the other entry point: the router widget's standalone shell at
``/widgets/asastats/<address>``, which is what
:func:`widgethost.registry.swap_entry_url` sends a reader to once they have
chosen -- or defaulted to -- this router.

**Why this file exists at all.** None of the four router shells had functional
coverage. asastats was discovered by manifest, offered on the settings page,
and (sorting first among the swap routers) was the default for every profile
that had never chosen one -- while its URLs were not mounted and its entry URL
resolved to the empty string. Nothing failed loudly, because ``swap_entry_url``
returns "" when the name will not reverse, and no test ever loaded the page.

Nothing here touches a wallet, so nothing signs or submits. The wallet bridge
is absent in a bare browser, which is exactly the state a reader is in before
connecting, and is the state these assertions describe.
"""

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By

from walletauth.models import LinkedAddress

from .base import FunctionalTest

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


class AsastatsRouterPageTest(FunctionalTest):
    """Load the ASA Stats router shell as a reader who owns the address."""

    def _link_address(self, email="asastats-router@example.com"):
        """Log a user in and connect ADDRESS to them, which is what gates swap."""
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
        user.profile.preferred_router = "asastats"
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def _open_page(self):
        """Load the router's own shell page the way `swap_entry_url` sends one."""
        self.browser.get(f"{self.server_url}/widgets/asastats/{ADDRESS}")
        return self.find_elem_by_id("id-swap-swap")

    def test_the_router_page_loads_rather_than_404ing(self):
        """The whole point of publishing: this URL used to resolve to "".

        Asserted through the reader's eyes - a heading they can see - rather
        than on a status code, because a Django view can return 200 and render
        an error shell.
        """
        self._link_address()
        self._open_page()

        assert "Swap" in self.find_elem_by_class("swap-page-title").text
        assert "ASA Stats Smart Router" in self.browser.title

    def test_the_shell_carries_the_two_endpoint_urls_the_controller_needs(self):
        """`swap.js`'s adapter reads these off the shell; empty means no quote.

        This is the difference between our router and Folks or Haystack: there
        is no SDK bundle and no vendor configuration, so these two attributes
        *are* the configuration, and a template that stopped emitting one would
        leave the panel looking fine and unable to quote.
        """
        self._link_address()
        shell = self._open_page()

        assert shell.get_attribute("data-router") == "asastats"
        assert shell.get_attribute("data-quote-url").endswith("/quote")
        assert shell.get_attribute("data-group-url").endswith("/group")

    def test_no_vendor_configuration_reaches_the_browser(self):
        """Ours quotes in the engine, so there is nothing here worth tampering
        with - and no API key to leak. The Folks shell carries network,
        referrer and fee; this one must not.
        """
        self._link_address()
        shell = self._open_page()

        for attribute in ("data-network", "data-referrer", "data-fee-bps"):
            assert shell.get_attribute(attribute) is None, attribute

    def test_the_owned_address_is_offered_with_a_lazy_holdings_panel(self):
        """One `<details>` per linked address, each naming its holdings URL.

        The panel body is empty until the reader opens it - `swap.js` loads it
        on the first `toggle` - so the assertion is that the *seam* is present
        and addressed, not that holdings are rendered.
        """
        self._link_address()
        self._open_page()

        rows = self.find_elems_by_css("#id-swap-addresses li[data-address]")
        assert len(rows) == 1
        assert rows[0].get_attribute("data-address") == ADDRESS

        panel = rows[0].find_element(By.CSS_SELECTOR, ".id-swap-panel")
        assert ADDRESS in panel.get_attribute("data-holdings-url")
        assert panel.text.strip() == ""

    def test_opening_the_address_reveals_the_panel_seam(self):
        """A reader can actually open the row: `<details>` is not decorative."""
        self._link_address()
        self._open_page()

        details = self.find_elem_by_css("#id-swap-addresses details.swap-address")
        assert details.get_attribute("open") is None

        details.find_element(By.TAG_NAME, "summary").click()
        self.wait_until(
            lambda: self.find_elem_by_css(
                "#id-swap-addresses details.swap-address"
            ).get_attribute("open")
            is not None
        )

    def test_the_page_loads_without_javascript_errors(self):
        """`swap.js` runs here with no router SDK beside it and no wallet.

        The bridge (`window.asastatsSwap`) ships with the wallet bundle and is
        absent in a bare browser. The controller has to tolerate that rather
        than throwing, because it is every reader's state before connecting.
        """
        self._link_address()
        self.record_javascript_errors()
        self._open_page()

        assert self.javascript_errors() == []


class AsastatsRouterPageUnlinkedTest(FunctionalTest):
    """A reader who does not own the address gets told, not offered a swap."""

    def test_an_unlinked_reader_is_told_to_connect_rather_than_shown_holdings(self):
        """Ownership gates the panel, and the message has to be visible.

        The locked notice and the address list are mutually exclusive in the
        template; asserting both directions is what stops a future edit
        rendering the panel for someone who does not own the address.
        """
        session_cookie = self.create_session_cookie(
            username="asastats-unlinked@example.com",
            password="top_secret",
            permission=100,
        )
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        self.browser.get(f"{self.server_url}/widgets/asastats/{ADDRESS}")

        locked = self.find_elem_by_id("id-swap-locked")
        assert locked.is_displayed()
        assert "Connect the wallet" in locked.text

        # `find_elems_by_css` waits for presence *before* returning the list,
        # so it can never express absence - asked for something that is not
        # there it times out rather than returning []. The driver's own
        # `find_elements` returns an empty list immediately, which is the only
        # way to assert a thing is missing.
        assert self.browser.find_elements(By.CSS_SELECTOR, "#id-swap-addresses") == []
