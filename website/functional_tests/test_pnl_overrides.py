"""Functional tests for the reader's own figures in the profit and loss widget.

The engine is patched with answers shaped as `test_pnl_integration.py` and the
widget's unit tests have them; the calls themselves are covered there.
"""

import time
from unittest import mock

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from widgets.inhouse.pnl.models import PnlOverride

from .base import COOKIE_SEED_URL, FunctionalTest

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
BUNDLE = "0123456789abcdef0123456789abcdef01234567"
ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
INTRO = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
DEPOSIT = "DEPOSIT/GROUP+ID="
ASSET = {
    "asset": "777",
    "lp": False,
    "name": "Unpriced Token",
    "unit": "NOPR",
    "decimals": 0,
    "quantity": 10,
    "average_cost": 0.0,
    "price": None,
    "value": None,
    "cost": 0,
    "unrealized": None,
    "realized": 0,
    "income": 0,
    "expenses": 0,
    "total": 0,
    "return": None,
    "missing_quantity": 0,
    "unpriced": 1,
}
#: The asset's one event: a deposit without a price.
EVENT = {
    "date": 1_700_000_000,
    "id": DEPOSIT,
    "asset": "777",
    "kind": "deposit",
    "quantity": 10,
    "value": None,
    "cost": 0,
    "realized": None,
}


class PnlOverridesTest(FunctionalTest):
    """A reader sets a deposit's cost and an unpriced asset's value."""

    def setUp(self):
        super().setUp()
        patches = [
            mock.patch("core.context_processors.fetch_capabilities"),
            mock.patch(
                "widgets.inhouse.pnl.views.bundle_and_addresses_from_path",
                return_value=(BUNDLE, ADDRESS),
            ),
            mock.patch("widgets.inhouse.pnl.views._engine", side_effect=self._engine),
        ]
        capabilities, _, self.engine = [patch.start() for patch in patches]
        for patch in patches:
            self.addCleanup(patch.stop)
        capabilities.return_value = {"permission": 100}

    def _engine(self, scope, method, bundle, suffix="", **kwargs):
        """Answer each P&L endpoint for a processed bundle."""
        return {
            "events/": {},
            "evaluate/": {
                "currency": "usd",
                "assets": [ASSET],
                "totals": {"total": 0, "invested": 0, "value": 0},
            },
            "updating/": {"updating": None, "rows_at": 0},
            "asset/": {**ASSET, "events": [EVENT]},
        }.get(suffix, {})

    def _log_in(self, permission):
        cookie = self.create_session_cookie(
            username="pnl@example.com", password="top_secret", permission=permission
        )
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(cookie)
        return get_user_model().objects.get(username="pnl@example.com")

    def _open(self):
        self.browser.get(f"{self.server_url}/widgets/pnl/{ADDRESS}")

    def _wait_for(self, condition, timeout=10):
        deadline = time.time() + timeout
        while not condition() and time.time() < deadline:
            time.sleep(0.1)
        self.assertTrue(condition())

    def _sent_overrides(self):
        return [
            call.kwargs["json"]["overrides"]
            for call in self.engine.call_args_list
            if "overrides" in call.kwargs.get("json", {})
        ]

    def test_a_reader_sets_a_value_for_an_unpriced_asset(self):
        user = self._log_in(ASASTATSER)
        self._open()
        self.find_elem_by_css(".pnl-more-cell button").click()
        self.find_elem_by_css("details.pnl-override > summary").click()
        self.find_elem_by_css("details.pnl-override input[name=amount]").send_keys(
            "0.25"
        )
        self.find_elem_by_css("details.pnl-override button[type=submit]").click()
        self._wait_for(lambda: PnlOverride.objects.filter(user=user).exists())
        override = PnlOverride.objects.get(user=user)
        self.assertEqual(
            (override.kind, override.asset, override.amount_text, override.currency),
            ("value", "777", "0.25", "usd"),
        )
        # the page goes back to the table, which now asks with the value
        self._wait_for(
            lambda: {"values": [{"asset": "777", "amount": "0.25", "currency": "usd"}]}
            in self._sent_overrides()
        )

    def test_a_reader_sets_and_removes_a_deposits_cost(self):
        user = self._log_in(ASASTATSER)
        self._open()
        self.find_elem_by_css(".pnl-more-cell button").click()
        self.find_elem_by_css(".pnl-table tbody th button.pnl-link").click()
        self.find_elem_by_css(".pnl-asset details.pnl-override > summary").click()
        self.find_elem_by_css(".pnl-asset input[name=amount]").send_keys("50")
        Select(self.find_elem_by_css(".pnl-asset select[name=currency]")).select_by_value(
            "algo"
        )
        self.find_elem_by_css(".pnl-asset button[type=submit]").click()
        self._wait_for(lambda: PnlOverride.objects.filter(user=user).exists())
        override = PnlOverride.objects.get(user=user)
        self.assertEqual(
            (override.kind, override.event, override.amount_text, override.currency),
            ("basis", DEPOSIT, "50", "algo"),
        )
        self._wait_for(lambda: "/widgets/pnl/" in self.browser.current_url)
        self.find_elem_by_css(".pnl-more-cell button").click()
        self.find_elem_by_css(".pnl-table tbody th button.pnl-link").click()
        note = self.find_elem_by_css(".pnl-asset .pnl-cell-note")
        self.assertEqual(note.text, "you paid 50 ALGO")
        self.find_elem_by_css(".pnl-asset details.pnl-override > summary").click()
        self.browser.find_element(
            By.XPATH, "//button[normalize-space()='Remove your cost']"
        ).click()
        self._wait_for(lambda: not PnlOverride.objects.filter(user=user).exists())

    def test_an_invalid_amount_is_explained(self):
        user = self._log_in(ASASTATSER)
        self._open()
        self.find_elem_by_css(".pnl-more-cell button").click()
        self.find_elem_by_css("details.pnl-override > summary").click()
        field = self.find_elem_by_css("details.pnl-override input[name=amount]")
        # past the browser's own check: the server's answer shows in the form
        self.browser.execute_script("arguments[0].type = 'text';", field)
        field.send_keys("many")
        self.find_elem_by_css("details.pnl-override button[type=submit]").click()
        error = self.find_elem_by_css(".pnl-override-error[role=alert]")
        self.assertIn("Enter a number.", error.text)
        self.assertFalse(PnlOverride.objects.filter(user=user).exists())

    def test_intro_readers_get_no_override_forms(self):
        self._log_in(INTRO)
        self._open()
        self.find_elem_by_css(".pnl-more-cell button").click()
        self.find_elem_by_css(".pnl-table tbody tr.pnl-closed, .pnl-table tbody tr")
        self.assertFalse(self.browser.find_elements(By.CSS_SELECTOR, ".pnl-override"))


WALLET = "LXJ3Q6RZ2TJ6VCJDFMSM4ZVNYYYE4KVSL3N2TYR23PLNCJCIXBM3NYTBYE"


class PnlWalletsTest(PnlOverridesTest):
    """A reader lists another wallet of theirs in Settings."""

    test_a_reader_sets_a_value_for_an_unpriced_asset = None
    test_a_reader_sets_and_removes_a_deposits_cost = None
    test_an_invalid_amount_is_explained = None
    test_intro_readers_get_no_override_forms = None

    def test_a_reader_adds_and_removes_a_wallet(self):
        user = self._log_in(ASASTATSER)
        self.browser.get(f"{self.server_url}/widgets/pnl/{ADDRESS}?tab=settings")
        self.find_elem_by_css("#id-pnl-wallets input[name=address]").send_keys(WALLET)
        self.find_elem_by_css("#id-pnl-wallets .pnl-wallet-add button").click()
        self._wait_for(lambda: PnlOverride.objects.filter(user=user).exists())
        self.assertEqual(PnlOverride.objects.get(user=user).event, WALLET)
        self.find_elem_by_css("#id-pnl-wallets .pnl-wallets li")
        self._open()
        self._wait_for(lambda: {"own": [WALLET]} in self._sent_overrides())
        self.browser.get(f"{self.server_url}/widgets/pnl/{ADDRESS}?tab=settings")
        self.find_elem_by_css("#id-pnl-wallets .pnl-wallets button").click()
        self._wait_for(lambda: not PnlOverride.objects.filter(user=user).exists())

    def test_a_bad_address_is_explained(self):
        self._log_in(ASASTATSER)
        self.browser.get(f"{self.server_url}/widgets/pnl/{ADDRESS}?tab=settings")
        self.find_elem_by_css("#id-pnl-wallets input[name=address]").send_keys("NOPE")
        self.find_elem_by_css("#id-pnl-wallets .pnl-wallet-add button").click()
        error = self.find_elem_by_css("#id-pnl-wallets [role=alert]")
        self.assertEqual(error.text, "That is not an Algorand address.")

    def test_intro_readers_have_no_wallets_section(self):
        self._log_in(INTRO)
        self.browser.get(f"{self.server_url}/widgets/pnl/{ADDRESS}?tab=settings")
        self.find_elem_by_link_text("Settings")
        self.assertFalse(self.browser.find_elements(By.ID, "id-pnl-wallets"))
