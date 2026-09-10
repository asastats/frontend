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

    def test_the_shell_carries_the_endpoint_urls_the_controller_needs(self):
        """`swap.js`'s adapter reads these off the shell; empty means no quote.

        This is the difference between our router and Folks or Haystack: there
        is no SDK bundle and no vendor configuration, so these attributes
        *are* the configuration, and a template that stopped emitting one would
        leave the panel looking fine and unable to quote.
        """
        self._link_address()
        shell = self._open_page()

        assert shell.get_attribute("data-router") == "asastats"
        assert shell.get_attribute("data-quote-url").endswith("/quote")
        assert shell.get_attribute("data-group-url").endswith("/group")
        # The third endpoint, for the wallets that rewrite what they sign. Its
        # absence is not a broken panel - the adapter simply reports the
        # divergence instead of fixing it - which is exactly why a template
        # that stopped emitting it would go unnoticed until a post-quantum
        # caller tried to swap.
        assert shell.get_attribute("data-reauthorize-url").endswith("/reauthorize")

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


class AsastatsRouterSwapOptInTest(FunctionalTest):
    """The opt-in the quote-signed path has to send *before* its group.

    A quote-signed group is signed by the backend over exact indices and its
    note records them, so `signAndSendPartial` refuses to prepend anything -
    correctly. The controller's partial branch returned before reaching the
    opt-in handling the array branch has, so nothing opted the caller in at
    all: four routed swaps in a row were refused on chain with `must optin,
    asset ... missing from <caller>` while three earlier ones, into assets
    already held, went through.

    Jest covers the ordering in isolation. What it cannot cover is that the
    real page reaches this code with a real quote in hand, which is what the
    two browser-only failures behind it were made of - so this drives the
    shipped page end to end and asserts on the order the bridge is called in.

    Nothing signs: the bridge is a recorder.
    """

    FROM_ASSET = 31566704  # USDC, held
    TO_ASSET = 393537671   # not held, so the swap has to opt in first

    def setUp(self):
        """Silence the capabilities call the shell's context processor makes.

        It reaches the engine on :8001, which is not running for a test - and
        the failure lands in a context processor, so the page renders as an
        error and every wait here times out. That reads as a broken swap panel
        rather than as one missing mock.
        """
        super().setUp()
        from unittest import mock

        patched = mock.patch("core.context_processors.fetch_capabilities")
        capabilities = patched.start()
        self.addCleanup(patched.stop)
        capabilities.return_value = {"permission": 100}

    def _link_address(self, email="asastats-optin@example.com"):
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
        # The adapter POSTs same-origin and sends `csrftoken` as a header for
        # Django to compare against the cookie. A browser that has never
        # submitted a form carries neither, and the quote is then refused
        # before it reaches the view - which reads exactly like a broken
        # adapter. Any value does: Django compares the two, not their contents.
        self.browser.add_cookie({"name": "csrftoken", "value": "x" * 64})
        return user

    def _holdings(self):
        """What the address holds: the input asset, and never the target."""
        return {
            "0": {"name": "Algorand", "unit": "ALGO", "decimals": 6, "amount": 5_000_000},
            str(self.FROM_ASSET): {
                "name": "USDC",
                "unit": "USDC",
                "decimals": 6,
                "amount": 10_000_000,
            },
        }

    def _quote(self):
        """A sell quote in the shape `AsastatsAdapter.getQuote` reads."""
        return {
            "amount_in": "1000000",
            "amount_out": "2500000",
            "minimum_received": "2487500",
            "maximum_sent": "1000000",
            "price_impact_pct": 0.12,
            "value_usdc": 1.0,
            "route_label": "Tinyman",
            "fees_total": 3000,
            "mode": "sell",
            "asset_in": self.FROM_ASSET,
            "asset_out": self.TO_ASSET,
        }

    def _built_group(self):
        """A routed group: the partial shape, which is the one that cannot prepend."""
        from base64 import b64encode

        return {
            "transactions": [b64encode(bytes([0x80 + n])).decode() for n in range(3)],
            "signed_transactions": {"2": b64encode(bytes([0x8A])).decode()},
            "quote_signer_index": 2,
        }

    def _install_recording_bridge(self):
        """A bridge that records the order it is called in and resolves.

        The order is the entire assertion. Opting in *after* submitting fails
        exactly as not opting in at all does, so a recorder that only counted
        calls would pass on the bug this exists for.
        """
        self.browser.execute_script(
            "var address = arguments[0];"
            "window.__calls = [];"
            "window.asastatsSwap = {"
            "  activeAddress: function () { return address; },"
            "  optIn: function (assetId) {"
            "    window.__calls.push({ call: 'optIn', asset: assetId });"
            "    return Promise.resolve('OPTED');"
            "  },"
            "  signAndSendPartial: function (group) {"
            "    window.__calls.push({"
            "      call: 'signAndSendPartial',"
            "      transactions: group.transactions.length,"
            "      signerIndex: group.quoteSignerIndex"
            "    });"
            "    return Promise.resolve('TXID');"
            "  },"
            "  signAndSend: function () {"
            "    window.__calls.push({ call: 'signAndSend' });"
            "    return Promise.resolve('TXID');"
            "  }"
            "};"
            "window.dispatchEvent(new CustomEvent('asastats:swap-ready'));",
            ADDRESS,
        )

    def _panel_state(self):
        """Everything `executeSwap`'s first line depends on, read from the DOM.

        `readQuoteParams` returns null when any of from, to or amount is
        empty, and `executeSwap` then returns without touching the status or
        the button - a silent stop that looks identical to a click that never
        landed. Reading the three fields is what tells those apart.
        """
        return self.browser.execute_script(
            "var p = document.querySelector('.id-swap-panel');"
            "if (!p) return null;"
            "var from = p.querySelector('.id-swap-from');"
            "var to = p.querySelector('.id-swap-to');"
            "var amount = p.querySelector('.id-swap-amount');"
            "var btn = p.querySelector('.id-swap-swap-btn');"
            "var status = p.querySelector('.id-swap-status');"
            "return {"
            "  from: from && from.value,"
            "  to: to && to.value,"
            "  optedIn: to && to.dataset.optedIn,"
            "  amount: amount && amount.value,"
            "  out: (p.querySelector('.id-swap-out') || {}).value,"
            "  label: btn && btn.textContent.trim(),"
            "  disabled: btn && btn.disabled,"
            "  status: status && status.textContent.trim(),"
            "  calls: window.__calls"
            "};"
        )

    def _open_and_quote(self):
        """Drive the page to a standing quote, and return the CTA."""
        self.browser.get(f"{self.server_url}/widgets/asastats/{ADDRESS}")
        self._install_recording_bridge()

        # **The panel does not exist until the row is opened.** Each linked
        # address is a `<details>` whose body `swap.js` fetches on the first
        # `toggle`, so before this click there is no source select, no target
        # input and no amount field - and `readQuoteParams` returns null on
        # all three. `executeSwap` then returns without touching the status or
        # the button, which is indistinguishable from a click that never
        # landed and is the trap this test spent seven runs in.
        self.find_elem_by_css(
            "#id-swap-addresses details.swap-address summary"
        ).click()

        # The holdings panel is lazy, so the source select is empty until it
        # arrives - and an empty source is one of the three things that makes
        # `readQuoteParams` return null.
        self.wait_until(
            lambda: self.browser.execute_script(
                "var s = document.querySelector('.id-swap-from');"
                "return !!(s && s.value);"
            )
        )

        # The picker lives in a sheet and its input is not interactable until
        # the pill opens it.
        self.find_elem_by_css('[data-swap-pick="to"]').click()
        search = self.wait_until(
            lambda: self.find_elem_by_css(".id-swap-to-search").is_displayed()
            and self.find_elem_by_css(".id-swap-to-search")
        )
        search.send_keys("gold")
        option = self.wait_until(
            lambda: self.browser.find_elements(
                By.CSS_SELECTOR, ".id-swap-asset-option"
            )
            and self.find_elem_by_css(".id-swap-asset-option")
        )
        option.click()

        self.find_elem_by_css(".id-swap-amount").send_keys("1")

        # The quote is debounced, so the wait is on the rendered result rather
        # than on the request having been made.
        self.wait_until(
            lambda: self.browser.execute_script(
                "var o = document.querySelector('.id-swap-out');"
                "return !!(o && o.value);"
            ),
            timeout=10,
        )
        return self.find_elem_by_css(".id-swap-swap-btn")

    def test_a_quote_signed_swap_opts_in_before_it_submits(self):
        """The order is the bug: opting in after submitting fails identically.

        Asserted on the bridge's own call log rather than on the panel text,
        because the panel says "Check your wallet" for both signatures and
        cannot distinguish them.
        """
        from unittest import mock

        self._link_address()
        answered = mock.Mock()
        answered.json.side_effect = [self._quote(), self._built_group()]
        with mock.patch(
            "widgets.inhouse.swapcore.views.fetch_account_holdings",
            return_value=self._holdings(),
        ), mock.patch(
            "widgets.inhouse.swapcore.views.fetch_asset_matches",
            return_value=[
                {
                    "id": self.TO_ASSET,
                    "unit": "GOLD$",
                    "name": "Meld Gold",
                    "decimals": 5,
                    "usdc_price": 0.9,
                    "verified": True,
                }
            ],
        ), mock.patch(
            "widgets.inhouse.asastats.views.engine_request", return_value=answered
        ):
            cta = self._open_and_quote()
            assert cta.is_enabled(), self._panel_state()
            cta.click()
            # Waiting on the panel reaching its terminal state rather than on
            # a call count: a missing opt-in still submits, so counting calls
            # would time out and report nothing about what actually happened.
            self.wait_until(
                lambda: self.browser.execute_script(
                    "var b = document.querySelector('.id-swap-swap-btn');"
                    "return b && /submitted|Try again/.test(b.textContent);"
                ),
                timeout=10,
            )
            calls = self.browser.execute_script("return window.__calls;")

        # The order is the assertion. Opting in after the group is submitted
        # fails on chain exactly as never opting in does, so a set comparison
        # would pass on the bug.
        assert [one["call"] for one in calls] == [
            "optIn",
            "signAndSendPartial",
        ], self._panel_state()
        assert calls[0]["asset"] == self.TO_ASSET
        assert calls[1]["transactions"] == 3
        assert calls[1]["signerIndex"] == 2
