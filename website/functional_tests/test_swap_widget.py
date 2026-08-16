"""Functional tests for the swap modal opened from the address page.

These drive the real templates, the real stylesheet and the real controller in a
browser, which is what the jest suite cannot do: it asserts against a hand-built
fixture, so a partial that stops emitting an element -- or a controller that
updates one half of a control and leaves the other half stale -- still passes
there. Everything the engine would answer is mocked; nothing here touches a
wallet, so no test signs or submits anything. The Swap button stays disabled
throughout ("Connect wallet to swap"), which is exactly the state a visitor
looking at quotes is in.
"""

import json
import os
from unittest import mock

from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from selenium.webdriver.common.by import By

from walletauth.models import LinkedAddress

from .base import FunctionalTest

SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "utils",
    "tests",
    "sample_serialized_540A5.json",
)

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"

# The engine's holdings shape: {asset_id: {name, unit, decimals, amount}}, amounts
# in base units. 5 ALGO and 2.5 USDC, so percentage chips land on round figures.
HOLDINGS = {
    "0": {"name": "Algorand", "unit": "ALGO", "decimals": 6, "amount": 5000000},
    "31566704": {"name": "USD Coin", "unit": "USDC", "decimals": 6, "amount": 2500000},
}

# The engine's assets:lookup shape, as _assets.html consumes it. USDC is in the
# pool as well as in the holdings, so a target that CAN become the source (flip)
# and one that cannot are both reachable through the real search.
ASSET_POOL = [
    {
        "id": 312769,
        "unit": "USDt",
        "name": "Tether USDt",
        "decimals": 6,
        "verified": True,
    },
    {
        "id": 31566704,
        "unit": "USDC",
        "name": "USD Coin",
        "decimals": 6,
        "verified": True,
    },
    {
        "id": 386192725,
        "unit": "goBTC",
        "name": "goBTC",
        "decimals": 8,
        "verified": True,
    },
]


def _matching_assets(query, _scopes):
    """Stand in for the engine's ranked lookup: unit prefix or exact asset id."""
    lowered = query.lower()
    return [
        asset
        for asset in ASSET_POOL
        if asset["unit"].lower().startswith(lowered) or query == str(asset["id"])
    ]


def _sample_payload():
    with open(SAMPLE_PATH) as sample_file:
        return json.load(sample_file)


@override_settings(
    # The address page is cache_page'd. A shared local-memory cache would let one
    # test method serve another's rendered page, so each test renders its own.
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
)
class SwapModalTest(FunctionalTest):
    """Open the redesigned swap modal and exercise its controls end to end."""

    def _link_address(self, email="swapper@example.com"):
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
        # Pin the router: the default is whichever swap widget sorts first, and
        # only the ones shipping an SDK bundle load cleanly in a bare browser.
        user.profile.preferred_router = "folks"
        user.profile.save()

        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(session_cookie)
        return user

    def _open_modal(self, from_asset="0"):
        """Load the address page and open the modal the way a user does.

        The Swap link sits inside a collapsed accordion body, so it is clicked
        through the DOM -- the click still bubbles to the delegated handler
        swap.js installs, which is the code path under test.
        """
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self._disarm_icon_fallback()
        self.accept_cookie()
        # htmx delivers the per-user marker, the modal and the controller.
        self.find_elem_by_id("id-swap-enabled")
        self.browser.execute_script(
            "document.querySelector"
            "('.id-swap-swap-toggle[data-from=\"%s\"]').click();" % from_asset
        )
        # It is a native <dialog> now, opened with showModal(): the `open`
        # attribute is the browser's own record that it is on the top layer.
        # The address page is the heaviest on the site -- charts, the asset
        # accordion, then an htmx panel load. Run on its own this test takes
        # ~35s on a Pi and passes; it only times out under full-suite load, so
        # the leash is long rather than the default 5s.
        self.wait_until(
            lambda: self.find_elem_by_id("swap-modal").get_attribute("open")
            is not None,
            timeout=30,
        )
        # The panel arrives by a second htmx request, gated on the linkage.
        form = self.find_elem_by_css(".id-swap-panel .id-swap-form")
        # Presence only means the HTML landed; bindPanel runs after the swap, so
        # wait for the pill it paints before asserting on anything it touches.
        self.wait_until(
            lambda: self.find_elem_by_css(".id-swap-from-unit").text
            not in ("", "Select"),
            timeout=30,
        )
        return form

    def _disarm_icon_fallback(self):
        """Stop the CDN fallback from rewriting the icons these tests read.

        Asset icons are real CDN URLs. A test machine that cannot reach the CDN
        -- or an asset that simply has no icon -- fires `error`, and swap.js
        answers by swapping the src for empty.png. Every icon assertion would
        then hold no matter what the controller did, which is worse than flaky:
        the test could not fail. A capture listener on the document runs before
        the panel's own (capture goes root-first), so stopping propagation there
        leaves each src exactly as the controller wrote it. The fallback itself
        is covered by the jest suite.

        Installed before the panel is requested, so it is in place ahead of the
        first icon request rather than racing it.
        """
        self.browser.execute_script(
            "document.addEventListener('error', function (ev) {"
            "  if (ev.target && ev.target.tagName === 'IMG') ev.stopPropagation();"
            "}, true);"
        )

    def _pill(self, side):
        """Return (unit text, icon src) for the "from" or "to" asset pill."""
        unit = self.find_elem_by_css(f".id-swap-{side}-unit").text
        icon = self.find_elem_by_css(f".id-swap-{side}-icon").get_attribute("src")
        return unit, icon

    def _click(self, selector):
        self.browser.execute_script(
            "document.querySelector(arguments[0]).click();", selector
        )

    def _result_rows(self):
        return self.browser.find_elements(
            By.CSS_SELECTOR, ".id-swap-to-results .id-swap-asset-option"
        )

    def _result_ids(self):
        return [row.get_attribute("data-id") for row in self._result_rows()]

    def _pick_target(self, query, asset_id):
        """Choose a receive asset the way a user does: open, search, click.

        Waits for the row carrying `asset_id` rather than for any row at all, so
        an earlier keystroke's result set can never be the one clicked.
        """
        self._click(".id-swap-to-btn")
        self.find_elem_by_css(".id-swap-to-search").send_keys(query)
        row = self.wait_until(
            lambda: self.browser.find_elements(
                By.CSS_SELECTOR,
                f'.id-swap-to-results .id-swap-asset-option[data-id="{asset_id}"]',
            )
        )[0]
        row.click()
        self.wait_until(
            lambda: self.find_elem_by_css(".id-swap-to").get_attribute("value")
            == str(asset_id)
        )
        return row

    def _mocks(self):
        """Patch every engine call the swap flow makes, for the whole test."""
        patches = [
            mock.patch("core.context_processors.fetch_capabilities"),
            mock.patch("core.views.check_export_status"),
            mock.patch("core.views.fetch_and_serialize_account"),
            mock.patch("widgets.inhouse.swapcore.views.fetch_account_holdings"),
            mock.patch("widgets.inhouse.swapcore.views.fetch_asset_matches"),
        ]
        started = [patch.start() for patch in patches]
        for patch in patches:
            self.addCleanup(patch.stop)
        capabilities, status, account, holdings, assets = started
        capabilities.return_value = {"permission": 100}
        status.return_value = {}
        account.return_value = _sample_payload()
        holdings.return_value = HOLDINGS
        assets.side_effect = _matching_assets
        return assets

    def setUp(self):
        super().setUp()
        self._mocked_assets = self._mocks()
        self._link_address()

    def test_swap_modal_opens_with_the_redesigned_shell(self):
        self._open_modal()

        self.assertEqual(self.find_elem_by_css(".swap-title").text, "Swap")
        # The router name is server-rendered, so it survives a panel that fails.
        self.assertEqual(
            self.find_elem_by_css(".swap-routertag").text, "Folks Smart Router"
        )
        self.assertEqual(self.find_elem_by_css(".id-swap-slip-value").text, "0.5%")
        modes = [button.text for button in self.find_elems_by_css("[data-swap-mode]")]
        self.assertEqual(modes, ["Sell an amount", "Buy an amount"])
        # Sell is the landing mode.
        self.assertEqual(
            self.find_elem_by_css('[data-swap-mode="sell"]').get_attribute(
                "aria-selected"
            ),
            "true",
        )

    def test_the_panel_lands_on_the_first_holding(self):
        self._open_modal()

        unit, icon = self._pill("from")
        self.assertEqual(unit, "ALGO")
        self.assertTrue(icon.endswith("/icons/0t.png"), icon)
        # "Available", not "Balance": for ALGO the engine sends
        # `amount - min-balance`, so this is smaller than the balance the rest
        # of the page shows for the same account, on purpose.
        self.assertEqual(self.find_elem_by_css(".id-swap-from-max").text, "5 ALGO")
        self.assertEqual(
            self.find_elem_by_css(".swap-leg-pay .swap-leg-bal").text,
            "Available 5 ALGO",
        )
        # Nothing chosen to receive yet.
        self.assertEqual(self.find_elem_by_css(".id-swap-to-unit").text, "Select token")

    def test_without_a_wallet_the_button_says_what_is_missing(self):
        self._open_modal()

        button = self.find_elem_by_css(".id-swap-swap-btn")
        self.assertEqual(button.text, "Connect wallet to swap")
        self.assertFalse(button.is_enabled())
        self.assertTrue(self.find_elem_by_css(".id-swap-connect-notice").is_displayed())

    def test_the_target_picker_searches_and_fills_the_pill(self):
        self._open_modal()

        self._click(".id-swap-to-btn")
        picker = self.find_elem_by_css(".id-swap-picker")
        self.assertIsNone(picker.get_attribute("hidden"))
        self.assertEqual(picker.get_attribute("data-side"), "to")
        self.assertEqual(
            self.find_elem_by_css(".id-swap-picker-title").text,
            "Select a token to receive",
        )

        self.find_elem_by_css(".id-swap-to-search").send_keys("USDt")
        # Keystrokes are debounced but not guaranteed to collapse into one
        # request, so settle on the final result set rather than the first.
        rows = self.wait_until(
            lambda: self._result_rows() if self._result_ids() == ["312769"] else None
        )
        rows[0].click()

        # Choosing closes the sheet and paints the pill from the row's data.
        self.assertEqual(
            self.wait_until(
                lambda: self.find_elem_by_css(".id-swap-picker").get_attribute("hidden")
            ),
            "true",
        )
        unit, icon = self._pill("to")
        self.assertEqual(unit, "USDt")
        self.assertTrue(icon.endswith("/icons/312769t.png"), icon)
        self.assertEqual(
            self.find_elem_by_css(".id-swap-to").get_attribute("value"), "312769"
        )

    def test_the_source_picker_lists_holdings_without_a_round_trip(self):
        self._open_modal()
        calls_before = self._mocked_assets.call_count

        self._click(".id-swap-from-btn")
        rows = self.find_elems_by_css(".id-swap-own-results .id-swap-own-option")
        self.assertEqual(
            [row.get_attribute("data-id") for row in rows], ["0", "31566704"]
        )

        rows[1].click()
        self.wait_until(lambda: self._pill("from")[0] == "USDC")
        unit, icon = self._pill("from")
        self.assertEqual(unit, "USDC")
        self.assertTrue(icon.endswith("/icons/31566704t.png"), icon)
        self.assertEqual(self.find_elem_by_css(".id-swap-from-max").text, "2.5 USDC")
        # The source list is rendered from the <select> already on the page.
        self.assertEqual(self._mocked_assets.call_count, calls_before)

    def test_switching_to_buy_repaints_the_target_pill_completely(self):
        """Regression: the unit moved with the mode and the icon did not.

        retargetForMode kept data-unit/decimals/opted-in on the hidden target in
        step but not data-icon, so clicking Buy left the previously chosen
        asset's icon sitting beside the newly locked target's name.
        """
        self._open_modal()

        self._pick_target("USDt", 312769)
        self.assertEqual(self._pill("to")[0], "USDt")
        self.assertTrue(self._pill("to")[1].endswith("/icons/312769t.png"))

        # Buy locks the target to the anchor (the asset the modal was opened on).
        self._click('[data-swap-mode="buy"]')
        unit, icon = self.wait_until(
            lambda: self._pill("to") if self._pill("to")[0] == "ALGO" else None
        )
        self.assertEqual(unit, "ALGO")
        self.assertTrue(icon.endswith("/icons/0t.png"), icon)

        # Back to Sell: the target is cleared, and so is its icon.
        self._click('[data-swap-mode="sell"]')
        unit, icon = self.wait_until(
            lambda: self._pill("to") if self._pill("to")[0] == "Select token" else None
        )
        self.assertTrue(icon.endswith("/icons/empty.png"), icon)

    def test_the_amount_field_moves_to_the_leg_it_belongs_to(self):
        """Sell fixes what you pay; Buy fixes what you receive."""
        self._open_modal()

        def slot_of(selector):
            return self.browser.execute_script(
                "var el = document.querySelector(arguments[0]);"
                "return el.parentElement.className;",
                selector,
            )

        self.assertIn("id-swap-slot-pay", slot_of(".id-swap-amount"))
        self.assertIn("id-swap-slot-get", slot_of(".id-swap-out"))

        self._click('[data-swap-mode="buy"]')
        self.wait_until(lambda: "id-swap-slot-get" in slot_of(".id-swap-amount"))
        self.assertIn("id-swap-slot-pay", slot_of(".id-swap-out"))

        self._click('[data-swap-mode="sell"]')
        self.wait_until(lambda: "id-swap-slot-pay" in slot_of(".id-swap-amount"))

    def test_percentage_chips_fill_the_amount_from_the_balance(self):
        self._open_modal()

        self._click('.id-swap-pct-btn[data-pct="50"]')
        amount = self.find_elem_by_css(".id-swap-amount")
        self.assertEqual(
            self.wait_until(lambda: amount.get_attribute("value") or None), "2.5"
        )

        self._click('.id-swap-pct-btn[data-pct="75"]')
        self.assertEqual(
            self.wait_until(
                lambda: (
                    amount.get_attribute("value")
                    if amount.get_attribute("value") != "2.5"
                    else None
                )
            ),
            "3.75",
        )

        # The engine already nets the minimum balance out of ALGO
        # (utils.clients._address_assets stores `amount - min-balance` at id 0),
        # so 5 is spendable ALGO. Max then keeps the group's own fees back on
        # top of that -- the swap has to be payable once the amount is set
        # aside. Nothing is opted into here, so it is the fee headroom alone.
        self._click('.id-swap-pct-btn[data-pct="100"]')
        self.assertEqual(
            self.wait_until(
                lambda: (
                    amount.get_attribute("value")
                    if amount.get_attribute("value") != "3.75"
                    else None
                )
            ),
            "4.97",
        )

    def test_slippage_presets_write_through_to_the_panel(self):
        self._open_modal()

        self._click(".id-swap-slip-toggle")
        popover = self.find_elem_by_css("#swap-slippage-pop")
        self.assertIsNone(popover.get_attribute("hidden"))

        self._click('.id-swap-slip-preset[data-slippage="1"]')
        # The header reads the new tolerance and the panel's hidden input, which
        # is what readQuoteParams actually quotes on, follows it.
        self.wait_until(
            lambda: self.find_elem_by_css(".id-swap-slip-value").text == "1%"
        )
        self.assertEqual(
            self.find_elem_by_css(".id-swap-slippage").get_attribute("value"), "1"
        )

    def test_a_risky_custom_slippage_is_called_out(self):
        self._open_modal()

        self._click(".id-swap-slip-toggle")
        self.find_elem_by_css(".id-swap-slip-custom").send_keys("40")
        warning = self.find_elem_by_css(".id-swap-slip-warn")
        self.wait_until(lambda: warning.is_displayed())
        self.assertTrue(warning.text.strip())

    def test_flipping_is_refused_until_both_sides_are_holdings(self):
        self._open_modal()
        flip = self.find_elem_by_css(".id-swap-flip")

        # Nothing chosen to receive: there is nothing to flip into.
        self.assertFalse(flip.is_enabled())

        # A target that is not held cannot become the source either.
        self._pick_target("USDt", 312769)
        self.assertFalse(self.find_elem_by_css(".id-swap-flip").is_enabled())

    def test_flipping_trades_two_held_assets_over(self):
        self._open_modal()

        # Pick a target the address does hold, so the sides can trade places.
        self._pick_target("USDC", 31566704)
        self.assertTrue(self.find_elem_by_css(".id-swap-flip").is_enabled())

        self._click(".id-swap-flip")

        self.wait_until(lambda: self._pill("from")[0] == "USDC")
        self.assertEqual(self._pill("to")[0], "ALGO")
        self.assertTrue(self._pill("to")[1].endswith("/icons/0t.png"))
        self.assertEqual(self.find_elem_by_css(".id-swap-from-max").text, "2.5 USDC")

    def test_the_picker_closes_without_choosing(self):
        self._open_modal()

        self._click(".id-swap-to-btn")
        self.assertIsNone(
            self.find_elem_by_css(".id-swap-picker").get_attribute("hidden")
        )
        self._click(".id-swap-picker-close")
        self.assertEqual(
            self.wait_until(
                lambda: self.find_elem_by_css(".id-swap-picker").get_attribute("hidden")
            ),
            "true",
        )
        self.assertEqual(self._pill("to")[0], "Select token")


class SwapModalUnlinkedTest(FunctionalTest):
    """An address that is not the viewer's offers no swap at all."""

    @mock.patch("widgets.inhouse.swapcore.views.fetch_account_holdings")
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_an_unlinked_viewer_gets_no_swap_marker(
        self, mocked_account, mocked_status, mocked_capabilities, mocked_holdings
    ):
        mocked_account.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 100}

        self.create_cookie_and_go_to_index_page_tier(
            "stranger@example.com", permission=100
        )
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.accept_cookie()

        # The gate is server-side: no marker, no modal, no controller, and the
        # engine is never asked for someone else's holdings.
        self.assertEqual(self.browser.find_elements(By.ID, "id-swap-enabled"), [])
        self.assertEqual(self.browser.find_elements(By.ID, "swap-modal"), [])
        mocked_holdings.assert_not_called()
