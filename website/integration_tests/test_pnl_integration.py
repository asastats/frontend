"""Integration tests for the P&L widget's engine seam.

Every call is made for a bundle nothing has processed, so it is safe to repeat
and does no work; why each answer matters is in docs/logbook.md under this
file's path.
"""

from django.test import TestCase

from api.client import BackendError, engine_request
from widgets.inhouse.pnl.manifest import MANIFEST

#: A bundle hash nothing has ever processed (the shape the engine expects).
UNKNOWN_BUNDLE = "0123456789abcdef0123456789abcdef01234567"

#: Every scope this widget declares, pinned so a new one forces a test.
DECLARED_SCOPES = {
    "pnl:asset",
    "pnl:evaluate",
    "pnl:events",
    "pnl:process",
    "pnl:reset",
}

#: The widget's default evaluate request, as `evaluate_payload` builds it.
EVALUATE = {"currency": "usd", "valuation": "spot", "method": "average"}


def _pnl(scope, method, suffix="", **kwargs):
    """Call the engine's P&L endpoint for the unknown bundle the way the widget does."""
    response = engine_request(
        scope,
        method,
        f"/api/v2/pnl/{UNKNOWN_BUNDLE}/{suffix}",
        MANIFEST.engine_endpoints,
        **kwargs,
    )
    return response.status_code, (response.json() if response.content else None)


class PnlScopeTest(TestCase):
    """The declarations, which need no engine."""

    def test_integration_pnl_declares_the_scopes_its_code_calls(self):
        self.assertEqual(set(MANIFEST.engine_endpoints), DECLARED_SCOPES)

    def test_integration_pnl_refuses_an_undeclared_scope_here(self):
        with self.assertRaises(BackendError):
            _pnl("historic:events", "GET", "events/")


class PnlUnprocessedBundleTest(TestCase):
    """What the engine answers for a bundle it has no rows for."""

    def test_integration_pnl_events_of_an_unknown_bundle_are_empty(self):
        self.assertEqual(_pnl("pnl:events", "GET", "events/"), (200, {}))

    def test_integration_pnl_evaluate_asks_for_an_update(self):
        self.assertEqual(
            _pnl("pnl:evaluate", "POST", "evaluate/", json=EVALUATE),
            (200, {"type": "show_update"}),
        )

    def test_integration_pnl_evaluate_without_nft_values(self):
        self.assertEqual(
            _pnl("pnl:evaluate", "POST", "evaluate/", json={**EVALUATE, "nfts": False}),
            (200, {"type": "show_update"}),
        )

    def test_integration_pnl_evaluate_refuses_a_non_boolean_nfts(self):
        with self.assertRaises(BackendError) as raised:
            _pnl("pnl:evaluate", "POST", "evaluate/", json={**EVALUATE, "nfts": "no"})
        self.assertEqual(raised.exception.status_code, 400)

    def test_integration_pnl_report_without_nft_values(self):
        payload = {**EVALUATE, "nfts": False, "page": "a4", "full": False, "hidden": []}
        self.assertEqual(
            _pnl("pnl:evaluate", "POST", "report/", json=payload),
            (200, {"type": "show_update"}),
        )

    def test_integration_pnl_chart_asks_for_an_update(self):
        self.assertEqual(
            _pnl("pnl:evaluate", "POST", "chart/", json={"currency": "usd"}),
            (200, {"type": "show_update"}),
        )

    def test_integration_pnl_updating_of_an_unknown_bundle(self):
        self.assertEqual(
            _pnl("pnl:events", "POST", "updating/", json={**EVALUATE, "nfts": False}),
            (200, {"updating": None, "rows_at": 0}),
        )

    def test_integration_pnl_asset_asks_for_an_update(self):
        self.assertEqual(
            _pnl("pnl:asset", "POST", "asset/", json={"asset": "0", **EVALUATE}),
            (200, {"type": "show_update"}),
        )

    def test_integration_pnl_history_asks_for_an_update(self):
        self.assertEqual(
            _pnl("pnl:asset", "POST", "history/", json={"currency": "usd"}),
            (200, {"type": "show_update"}),
        )

    def test_integration_pnl_history_refuses_an_unknown_method(self):
        with self.assertRaises(BackendError) as raised:
            _pnl("pnl:asset", "POST", "history/", json={"method": "lofo"})
        self.assertEqual(raised.exception.status_code, 400)

    def test_integration_pnl_reset_of_an_unknown_bundle(self):
        self.assertEqual(_pnl("pnl:reset", "DELETE"), (204, None))

    def test_integration_pnl_process_refuses_addresses_of_another_bundle(self):
        with self.assertRaises(BackendError) as raised:
            _pnl("pnl:process", "POST", "process/", json={"addresses": "NOTANADDRESS"})
        self.assertEqual(raised.exception.status_code, 400)


#: The reader's own figures, as `PnlAccessMixin.overrides` sends them.
OVERRIDES = {
    "basis": [{"id": "A" * 52, "asset": "0", "amount": "50.5", "currency": "usd"}],
    "values": [{"asset": "31566704", "amount": "1", "currency": "algo"}],
    "own": ["2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"],
}


class PnlOverridesTest(TestCase):
    """The engine reads the reader's own figures on every endpoint that takes them."""

    def test_integration_pnl_overrides_accepted_everywhere(self):
        for scope, suffix, payload, expected in (
            ("pnl:evaluate", "evaluate/", EVALUATE, {"type": "show_update"}),
            ("pnl:evaluate", "chart/", {"currency": "usd"}, {"type": "show_update"}),
            ("pnl:asset", "asset/", {"asset": "0", **EVALUATE}, {"type": "show_update"}),
            ("pnl:asset", "history/", {"currency": "usd"}, {"type": "show_update"}),
            ("pnl:events", "updating/", EVALUATE, {"updating": None, "rows_at": 0}),
            (
                "pnl:evaluate",
                "report/",
                {**EVALUATE, "page": "a4", "full": False, "hidden": []},
                {"type": "show_update"},
            ),
        ):
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    _pnl(scope, "POST", suffix, json={**payload, "overrides": OVERRIDES}),
                    (200, expected),
                )

    def test_integration_pnl_overrides_refuses_a_bad_figure(self):
        bad = {"values": [{"asset": "31566704", "amount": "-1", "currency": "usd"}]}
        with self.assertRaises(BackendError) as raised:
            _pnl("pnl:evaluate", "POST", "evaluate/", json={**EVALUATE, "overrides": bad})
        self.assertEqual(raised.exception.status_code, 400)
