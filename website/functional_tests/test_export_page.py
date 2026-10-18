"""Functional tests for the tax-export form's currency.

The engine is patched: the page asks it for the export's status, and the form
starts the export through it (the real calls are in
`integration_tests/test_export_integration.py`).
"""

import time
from unittest import mock

from django.contrib.auth import get_user_model

from .base import COOKIE_SEED_URL, FunctionalTest

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


class ExportPageCurrencyTest(FunctionalTest):
    """The CSV's currency: said on the form, sent with the export."""

    def setUp(self):
        super().setUp()
        patches = [
            mock.patch("core.context_processors.fetch_capabilities"),
            mock.patch("core.views.check_export_status"),
            mock.patch("core.helpers._start_export"),
        ]
        capabilities, status, self.start = [patch.start() for patch in patches]
        for patch in patches:
            self.addCleanup(patch.stop)
        capabilities.return_value = {"permission": 100}
        status.return_value = {}

    def _log_in(self, fiat):
        cookie = self.create_session_cookie(
            username="export@example.com", password="top_secret", permission=100
        )
        user = get_user_model().objects.get(username="export@example.com")
        user.profile.fiat = fiat
        user.profile.save()
        self.browser.get(self.server_url + COOKIE_SEED_URL)
        self.browser.add_cookie(cookie)

    def _open(self):
        self.browser.get(f"{self.server_url}/export/{ADDRESS}/")
        return self.find_elem_by_id("process_form")

    def _submit(self):
        """Press Process and wait for the export to be started, at most ten seconds."""
        self.find_elem_by_id("process").click()
        deadline = time.time() + 10
        while not self.start.called and time.time() < deadline:
            time.sleep(0.1)
        self.start.assert_called_once()
        return self.start.call_args.args[2]

    def test_an_anonymous_reader_is_told_usd(self):
        form = self._open()
        self.assertIn("Worth amounts in USD.", form.text)

    def test_a_euro_reader_is_told_eur(self):
        self._log_in("EUR")
        form = self._open()
        self.assertIn("Worth amounts in EUR, converted from USD", form.text)

    def test_a_euro_reader_starts_the_export_in_eur(self):
        self._log_in("EUR")
        self._open()
        self.assertEqual(self._submit().get("fiat"), "EUR")

    def test_a_dollar_reader_starts_the_export_as_before(self):
        self._log_in("USD")
        self._open()
        self.assertNotIn("fiat", self._submit())
