"""Functional tests for the profit and loss widget's NFT setting and value notes.

The engine is patched with answers shaped as `test_pnl_integration.py` and the
widget's unit tests have them; the calls themselves are covered there.
"""

import time
from unittest import mock

from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS
from widgets.inhouse.pnl.models import PnlSettings

from .base import COOKIE_SEED_URL, FunctionalTest

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
BUNDLE = "0123456789abcdef0123456789abcdef01234567"
PROFESSIONAL = SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
CLUSTER = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]
TRANSACTION = "A" * 52
#: One event of the NFT, as the drill-down and the history answer it.
EVENT = {
    "date": 1_700_000_000,
    "id": TRANSACTION,
    "asset": "671908166",
    "kind": "swap",
    "quantity": 1,
    "value": 627_030_000,
    "cost": 627_030_000,
    "realized": None,
    "description": "Rand Gallery purchase",
}
ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]

#: An evaluation with one appraised NFT, as the engine answers it.
RESULTS = {
    "currency": "usd",
    "assets": [
        {
            "asset": "671908166",
            "lp": False,
            "nft": True,
            "name": "Lost Pigs 0088",
            "unit": "OINK",
            "decimals": 0,
            "quantity": 1,
            "average_cost": 627_030_000.0,
            "price": 388_000_000.0,
            "value": 388_000_000,
            "cost": 627_030_000,
            "unrealized": -239_030_000,
            "realized": 0,
            "income": 0,
            "expenses": 0,
            "total": -239_030_000,
            "return": -0.38,
            "missing_quantity": 0,
            "unpriced": 0,
        }
    ],
    "totals": {
        "total": -239_030_000,
        "invested": 627_030_000,
        "value": 388_000_000,
        "nft_value": 388_000_000,
        "nfts": True,
    },
}


class PnlWidgetNftTest(FunctionalTest):
    """A reader's NFT choice, and what the table says about NFT values."""

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
        self.results = RESULTS
        self.points = []

    def _engine(self, scope, method, bundle, suffix="", **kwargs):
        """Answer each P&L endpoint for a processed bundle."""
        return {
            "events/": {},
            "evaluate/": self.results,
            "updating/": {"updating": None, "rows_at": 0},
            "chart/": {"currency": "usd", "points": self.points},
            "asset/": {**RESULTS["assets"][0], "events": [EVENT]},
            "history/": {
                "currency": "usd",
                "assets": {"671908166": RESULTS["assets"][0]},
                "events": [{**EVENT, "rate": 1.0}],
            },
        }.get(suffix, {})

    def _log_in(self, permission, count_nfts=None, explorer=""):
        cookie = self.create_session_cookie(
            username="pnl@example.com", password="top_secret", permission=permission
        )
        user = get_user_model().objects.get(username="pnl@example.com")
        if count_nfts is not None:
            PnlSettings.objects.create(user=user, count_nfts=count_nfts)
        user.profile.preferred_explorer = explorer
        user.profile.save()
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(cookie)
        self.cookie = cookie
        return user

    def _open(self, query=""):
        self.browser.get(f"{self.server_url}/widgets/pnl/{ADDRESS}{query}")

    def _evaluate_payloads(self):
        return [
            call.kwargs.get("json", {})
            for call in self.engine.call_args_list
            if call.args[3:4] == ("evaluate/",)
        ]

    def test_a_professional_reader_can_leave_nfts_out(self):
        user = self._log_in(PROFESSIONAL)
        self._open("?tab=settings")
        checkbox = self.find_elem_by_css("input[type=checkbox][name=count_nfts]")
        self.assertTrue(checkbox.is_selected())
        checkbox.click()
        self.find_elem_by_css("#id-pnl-settings-form button[type=submit]").click()
        self.find_elem_by_css("#id-pnl-settings-form [role=status]")
        self.assertFalse(PnlSettings.objects.get(user=user).count_nfts)

    def test_an_asastatser_reader_has_no_nft_choice(self):
        self._log_in(ASASTATSER)
        self._open("?tab=settings")
        self.find_elem_by_link_text("Settings")
        self.assertFalse(self.browser.find_elements(By.NAME, "count_nfts"))

    def test_the_table_marks_appraised_nfts_and_their_share(self):
        self._log_in(PROFESSIONAL)
        self._open()
        badge = self.find_elem_by_css(".pnl-table .pnl-badge-muted")
        self.assertEqual(badge.text.lower(), "appraised")
        self.assertIn("of the value is NFTs marked", self.browser.page_source)

    def test_a_reader_who_left_nfts_out_asks_without_them(self):
        self._log_in(PROFESSIONAL, count_nfts=False)
        self.results = {**RESULTS, "totals": {**RESULTS["totals"], "nfts": False}}
        self._open()
        self.find_elem_by_link_text("How these figures are made")
        self.assertIn(
            "NFTs are not valued, as chosen in Settings", self.browser.page_source
        )
        self.assertTrue(self._evaluate_payloads())
        for payload in self._evaluate_payloads():
            self.assertIs(payload.get("nfts"), False)

    def test_the_processed_time_follows_the_readers_timezone(self):
        self._log_in(ASASTATSER)
        self.browser.execute_cdp_cmd(
            "Emulation.setTimezoneOverride", {"timezoneId": "Asia/Tokyo"}
        )
        self.results = {**RESULTS, "processed_at": 1_760_000_000}
        self._open()
        processed = self.find_elem_by_css("time[data-local-time]")
        self.assertIn("GMT+9", processed.text)
        self.assertNotIn("UTC", processed.text)
        self.assertEqual(processed.get_attribute("datetime"), "2025-10-09T08:53:20Z")

    def test_a_reader_sees_what_a_reprocess_changed(self):
        self._log_in(ASASTATSER)
        change = {"quantity": -1, "cost": -627_030_000, "realized": 0.0}
        self.results = {
            **RESULTS,
            "changes": {
                "since": 1_760_000_000,
                "assets_changed": 1,
                "cost": -627_030_000,
                "realized": 0.0,
                "income": 0.0,
                "expenses": 0.0,
                "assets": [
                    {"asset": "671908166", **change, "income": 0.0, "expenses": 0.0}
                ],
            },
        }
        self._open()
        summary = self.find_elem_by_css("details.pnl-issues > summary")
        self.assertIn("What changed when the history was processed again", summary.text)
        row = self.browser.find_element(
            By.XPATH, "//details[summary[contains(., 'What changed')]]//tbody/tr"
        )
        self.assertFalse(row.is_displayed())
        summary.click()
        self.assertTrue(row.is_displayed())
        self.assertIn("OINK", row.text)
        self.assertIn("-$627.03", row.text)

    def test_the_drilldown_links_each_transaction_to_the_readers_explorer(self):
        self._log_in(ASASTATSER, explorer="pera")
        self._open()
        self.find_elem_by_css(".pnl-table tbody th button.pnl-link").click()
        link = self.find_elem_by_css(".pnl-asset a.pnl-txid")
        self.assertEqual(
            link.get_attribute("href"),
            f"https://explorer.perawallet.app/tx/{TRANSACTION}",
        )
        self.assertEqual(link.get_attribute("target"), "_blank")

    def test_insights_follow_the_tier(self):
        for permission, winners, concentration in (
            (ASASTATSER, True, False),
            (PROFESSIONAL, True, True),
        ):
            with self.subTest(permission=permission):
                self._log_in(permission)
                self._open()
                self.find_elem_by_link_text("How these figures are made")
                source = self.browser.page_source
                self.assertEqual("Winners and losers" in source, winners)
                self.assertEqual("Concentration" in source, concentration)

    def test_the_losers_list_names_the_nft(self):
        self._log_in(ASASTATSER)
        self._open()
        cell = self.browser.find_element(
            By.XPATH, "//section[@class='pnl-insights']//tbody/tr/th"
        )
        self.assertEqual(cell.text, "OINK")

    def test_the_chart_states_its_largest_fall(self):
        self._log_in(PROFESSIONAL)
        self.points = [
            {"date": 1_700_000_000, "pnl": 0.0},
            {"date": 1_700_086_400, "pnl": 5_000_000},
            {"date": 1_700_172_800, "pnl": 1_000_000},
        ]
        self._open()
        note = self.find_elem_by_css(".pnl-chart-figure p.pnl-muted")
        self.assertEqual(
            note.text, "Largest fall: -$4.00, from 15 Nov 2023 to 16 Nov 2023."
        )

    def test_the_table_links_the_methodology(self):
        self._log_in(PROFESSIONAL)
        self._open()
        self.find_elem_by_link_text("How these figures are made").click()
        deadline = time.time() + 10
        while "/methodology/" not in self.browser.current_url and time.time() < deadline:
            time.sleep(0.1)
        self.assertTrue(self.browser.current_url.endswith("/methodology/"))
