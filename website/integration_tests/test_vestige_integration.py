"""Integration tests of the Vestige-compatible prices, through to the engine.

They need the backend's deployment token to carry the scope `prices:read`;
without it every price request here answers 503.
"""

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from api.client import prices_latest

URL = "/api/vestige/assets/price"
USDC = 31566704
KEYS = [
    "network_id",
    "asset_id",
    "denominating_asset_id",
    "price",
    "confidence",
    "total_lockup",
]


class VestigePricesIntegrationTest(TestCase):
    """Testing class for the Vestige-compatible prices fetched from the engine."""

    def setUp(self):
        cache.clear()

    def test_vestige_integration_engine_answers_in_request_order(self):
        prices = prices_latest([USDC, 0, 999999999999], "algo")
        self.assertEqual([entry["asset_id"] for entry in prices], [USDC, 0, 999999999999])
        self.assertEqual(prices[1]["price"], 1.0)
        self.assertIsNone(prices[2]["price"])

    def test_vestige_integration_prices_in_usdc(self):
        response = APIClient().get(
            URL, {"asset_ids": f"{USDC},0,999999999999", "denominating_asset_id": USDC}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        usdc, algo, unknown = response.json()
        for entry in (usdc, algo, unknown):
            self.assertEqual(list(entry), KEYS)

        self.assertAlmostEqual(usdc["price"], 1.0, places=6)
        self.assertEqual(usdc["confidence"], 1.0)
        # ALGO has cost between a cent and ten dollars for all of its history
        self.assertTrue(0.01 < algo["price"] < 10)
        self.assertEqual(
            unknown,
            {
                "network_id": 0,
                "asset_id": 999999999999,
                "denominating_asset_id": USDC,
                "price": 0.0,
                "confidence": 0.0,
                "total_lockup": 0.0,
            },
        )

    def test_vestige_integration_prices_in_algo_agree_with_usdc(self):
        in_algo = APIClient().get(URL, {"asset_ids": f"{USDC},0"}).json()
        in_usdc = (
            APIClient().get(URL, {"asset_ids": "0", "denominating_asset_id": USDC}).json()
        )
        self.assertEqual(in_algo[1]["price"], 1.0)
        # ALGO per USDC times USDC per ALGO, read a moment apart
        self.assertAlmostEqual(in_algo[0]["price"] * in_usdc[0]["price"], 1.0, places=2)
