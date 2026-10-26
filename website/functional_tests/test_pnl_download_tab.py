"""Functional tests for the profit and loss widget's Download tab.

The engine is patched with the answers `test_pnl_widget.py` uses; the calls
themselves are covered by the widget's unit tests.
"""

import types
from unittest import mock

import requests

from selenium.webdriver.common.by import By

from api.client import BackendError

from .base import COOKIE_SEED_URL, FunctionalTest
from .test_pnl_widget import (
    ADDRESS,
    BUNDLE,
    CLUSTER,
    EVENT,
    PROFESSIONAL,
    RESULTS,
    TRANSACTION,
)

PDF = b"%PDF-1.7 report"


class PnlDownloadTabTest(FunctionalTest):
    """The CSV files and the PDF report live on their own tab."""

    def setUp(self):
        super().setUp()
        patches = [
            mock.patch("core.context_processors.fetch_capabilities"),
            mock.patch(
                "widgets.inhouse.pnl.views.bundle_and_addresses_from_path",
                return_value=(BUNDLE, ADDRESS),
            ),
            mock.patch("widgets.inhouse.pnl.views._engine", side_effect=self._engine),
            mock.patch("widgets.inhouse.pnl.views.engine_request"),
        ]
        capabilities, _, _, self.engine_request = [patch.start() for patch in patches]
        for patch in patches:
            self.addCleanup(patch.stop)
        capabilities.return_value = {"permission": 100}
        self.engine_request.return_value = types.SimpleNamespace(content=PDF)

    def _engine(self, scope, method, bundle, suffix="", **kwargs):
        """Answer each P&L endpoint for a processed bundle."""
        return {
            "events/": {},
            "evaluate/": RESULTS,
            "updating/": {"updating": None, "rows_at": 0},
            "chart/": {"currency": "usd", "points": []},
            "report/": {"type": "ready", "key": "k_a4"},
            "history/": {
                "currency": "usd",
                "assets": {"671908166": RESULTS["assets"][0]},
                "events": [{**EVENT, "rate": 1.0}],
            },
        }.get(suffix, {})

    def _log_in(self, permission):
        self.cookie = self.create_session_cookie(
            username="pnl@example.com", password="top_secret", permission=permission
        )
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(self.cookie)

    def _open(self, query=""):
        self.browser.get(f"{self.server_url}/widgets/pnl/{ADDRESS}{query}")

    def _tabs(self):
        return self.find_elems_by_css("nav.pnl-tabs a")

    def _get(self, href):
        return requests.get(
            href, cookies={self.cookie["name"]: self.cookie["value"]}, timeout=30
        )

    def test_the_download_tab_sits_between_profit_and_loss_and_settings(self):
        self._log_in(CLUSTER)
        self._open()
        self.assertEqual(
            [tab.text for tab in self._tabs()],
            ["Profit and loss", "Download", "Settings"],
        )
        self.find_elem_by_link_text("Download").click()
        self.find_elem_by_id("id-pnl-download")
        self.assertIn("tab=download", self.browser.current_url)
        current = [tab.text for tab in self._tabs() if tab.get_attribute("aria-current")]
        self.assertEqual(current, ["Download"])

    def test_the_download_tab_offers_both_csvs_and_the_pdf_report(self):
        self._log_in(CLUSTER)
        self._open("?tab=download")
        panel = self.find_elem_by_id("id-pnl-download")
        self.assertTrue(panel.find_element(By.LINK_TEXT, "Download CSV").is_displayed())
        self.assertTrue(
            panel.find_element(By.LINK_TEXT, "Download events CSV").is_displayed()
        )
        report = panel.find_element(By.ID, "id-pnl-report")
        self.assertEqual(
            report.find_element(By.CSS_SELECTOR, "button[type=submit]").text,
            "Prepare PDF report",
        )
        self.assertEqual(self.browser.find_elements(By.ID, "id-pnl-body"), [])

    def test_the_table_no_longer_carries_the_downloads(self):
        self._log_in(CLUSTER)
        self._open()
        self.find_elem_by_link_text("How these figures are made")
        for text in ("Download CSV", "Download events CSV"):
            with self.subTest(text=text):
                self.assertEqual(self.browser.find_elements(By.LINK_TEXT, text), [])
        self.assertEqual(self.browser.find_elements(By.ID, "id-pnl-report"), [])

    def test_a_tier_without_downloads_has_no_download_tab(self):
        self._log_in(PROFESSIONAL)
        self._open("?tab=download")
        self.find_elem_by_link_text("How these figures are made")
        self.assertEqual(
            [tab.text for tab in self._tabs()], ["Profit and loss", "Settings"]
        )
        self.assertEqual(self.browser.find_elements(By.ID, "id-pnl-download"), [])

    def test_the_switches_stay_on_the_download_tab(self):
        self._log_in(CLUSTER)
        self._open("?tab=download")
        self.find_elem_by_css("nav[aria-label=Period]").find_element(
            By.LINK_TEXT, "30 days"
        ).click()
        self.wait_until(lambda: "period=30d" in self.browser.current_url)
        self.assertIn("tab=download", self.browser.current_url)
        href = self.find_elem_by_link_text("Download CSV").get_attribute("href")
        self.assertIn("period=30d", href)

    def test_the_csv_downloads_from_the_download_tab(self):
        self._log_in(CLUSTER)
        self._open("?tab=download")
        response = self._get(
            self.find_elem_by_link_text("Download CSV").get_attribute("href")
        )
        self.assertEqual(response.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertTrue(
            response.headers["Content-Disposition"].startswith(
                f'attachment; filename="pnl-{BUNDLE[:8]}-'
            )
        )
        self.assertIn("Lost Pigs 0088", response.content.decode("utf-8-sig"))

    def test_the_events_csv_downloads_every_event(self):
        self._log_in(CLUSTER)
        self._open("?tab=download")
        href = self.find_elem_by_link_text("Download events CSV").get_attribute("href")
        response = self._get(href)
        self.assertEqual(response.headers["Content-Type"], "text/csv; charset=utf-8")
        lines = response.content.decode("utf-8-sig").splitlines()
        self.assertTrue(lines[0].startswith("Date (UTC),Transaction ID,"))
        self.assertIn(TRANSACTION, lines[1])
        self.assertIn("Rand Gallery purchase", lines[1])

    def test_the_pdf_report_is_prepared_and_downloaded_on_the_download_tab(self):
        self._log_in(CLUSTER)
        self._open("?tab=download")
        self.find_elem_by_css("#id-pnl-report button[type=submit]").click()
        link = self.find_elem_by_link_text("Download PDF report")
        self.assertIn("tab=download", self.browser.current_url)
        response = self._get(link.get_attribute("href"))
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertEqual(response.content, PDF)

    def test_a_prepared_report_is_still_there_after_another_tab(self):
        self._log_in(CLUSTER)
        self._open("?tab=download")
        self.find_elem_by_css("#id-pnl-report button[type=submit]").click()
        self.find_elem_by_link_text("Download PDF report")

        self.find_elem_by_link_text("Profit and loss").click()
        self.find_elem_by_id("id-pnl-body")
        self.find_elem_by_link_text("Download").click()

        link = self.find_elem_by_link_text("Download PDF report")
        self.assertIn("key=k_a4", link.get_attribute("href"))
        self.assertNotIn("Prepare PDF report", self.browser.page_source)

    def test_a_report_never_asked_for_is_not_prepared_by_opening_the_tab(self):
        self._log_in(CLUSTER)
        self._open("?tab=download")
        self.find_elem_by_css("#id-pnl-report button[type=submit]")
        self.assertNotIn("Download PDF report", self.browser.page_source)

    def test_an_expired_report_comes_back_to_the_download_tab(self):
        self.engine_request.side_effect = BackendError("404: gone")
        self._log_in(CLUSTER)
        self._open("/report/download?key=k_old")
        self.find_elem_by_id("id-pnl-download")
        self.assertIn("tab=download", self.browser.current_url)
        self.assertIn("no longer available", self.browser.page_source)
