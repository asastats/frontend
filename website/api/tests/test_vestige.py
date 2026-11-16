"""Testing module for :py:mod:`api.vestige` and :py:mod:`api.urls_vestige` modules.

The contract tests compare our answers with responses saved from Vestige on
2026-11-15 (`fixtures/vestige/`): same keys, same order, same types.
"""

import json
from pathlib import Path

import pytest
from django.urls import resolve
from rest_framework.test import APIClient

from api import vestige
from api.client import BackendError
from api.vestige import VestigeAssetPricesView, VestigeRateThrottle
from utils.constants.apiv2 import VESTIGE_MAX_ASSETS, VESTIGE_PRICE_CACHE_SECONDS

FIXTURES = Path(__file__).parent / "fixtures" / "vestige"
URL = "/api/vestige/assets/price"
GOBTC, USDC = 386192725, 31566704


def saved(name):
    """Return a response body saved from Vestige."""
    return json.loads((FIXTURES / name).read_text())


def entry(asset_id, price=None, lockup=None):
    """Return an engine price entry."""
    return {
        "asset_id": asset_id,
        "price": price,
        "timestamp": 1_800_000_000 if price else None,
        "source": "live" if price else None,
        "depth_algo": None,
        "lockup": lockup,
    }


@pytest.fixture
def latest(mocker):
    """Return the mocked engine call, answering every asset asked for."""
    return mocker.patch(
        "api.vestige.client.prices_latest",
        side_effect=lambda asset_ids, quote: [
            entry(asset_id, *({GOBTC: (64000.5, 0.11), 0: (1, None)}.get(asset_id, ())))
            for asset_id in asset_ids
        ],
    )


class TestApiVestigeUrls:
    """Testing class for :py:mod:`api.urls_vestige` module."""

    @pytest.mark.parametrize("path", [URL, URL + "/"])
    def test_api_vestige_urls_asset_prices(self, path):
        match = resolve(path)
        assert match.func.view_class is VestigeAssetPricesView
        assert match.url_name == "api_vestige_asset_prices"

    def test_api_vestige_urls_every_listed_path_has_its_view(self):
        for _pattern, view, _name in vestige.VESTIGE_PATHS:
            assert issubclass(getattr(vestige, view), vestige.VestigeView)

    def test_api_vestige_urls_other_paths_are_not_served(self):
        assert APIClient().get("/api/vestige/assets/list").status_code == 404


class TestApiVestigeAssetPricesContract:
    """Testing class for the shape of :class:`api.vestige.VestigeAssetPricesView`."""

    @pytest.mark.parametrize(
        "name,query",
        [
            ("price.json", f"asset_ids={GOBTC},{USDC},0"),
            (
                "price-usdc.json",
                f"asset_ids={GOBTC},0,999999999999&network_id=0"
                f"&denominating_asset_id={USDC}",
            ),
        ],
    )
    def test_api_vestige_prices_match_the_saved_shape(self, latest, name, query):
        response = APIClient().get(f"{URL}?{query}")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        ours, theirs = json.loads(response.content), saved(name)
        assert isinstance(ours, list) and len(ours) == len(theirs)
        for our, their in zip(ours, theirs):
            assert list(our) == list(their)
            assert {key: type(value) for key, value in our.items()} == {
                key: type(value) for key, value in their.items()
            }
            assert [our[key] for key in list(our)[:3]] == [
                their[key] for key in list(their)[:3]
            ]

    def test_api_vestige_prices_unknown_asset_is_zeros_as_saved(self, latest):
        response = APIClient().get(
            f"{URL}?asset_ids=999999999999&denominating_asset_id={USDC}"
        )
        assert json.loads(response.content) == [saved("price-usdc.json")[2]]

    def test_api_vestige_prices_missing_asset_ids_is_the_saved_422(self, latest):
        response = APIClient().get(URL)
        assert response.status_code == 422
        assert json.loads(response.content) == saved("err-missing-ids.json")

    @pytest.mark.parametrize(
        "asset_ids", ["abc", "5,abc", "5,,6", "-5", "", "1.5", 2**64]
    )
    def test_api_vestige_prices_bad_asset_ids_is_the_saved_400(self, latest, asset_ids):
        response = APIClient().get(URL, {"asset_ids": asset_ids})
        assert response.status_code == 400
        assert json.loads(response.content) == saved("err-bad-id.json")
        latest.assert_not_called()


class TestApiVestigeAssetPricesView:
    """Testing class for :class:`api.vestige.VestigeAssetPricesView`."""

    def test_api_vestige_prices_values_and_the_engine_call(self, latest):
        response = APIClient().get(
            URL, {"asset_ids": f" {GOBTC},0, 007", "denominating_asset_id": USDC}
        )
        latest.assert_called_once_with([GOBTC, 0, 7], "usd")
        assert response.json() == [
            {
                "network_id": 0,
                "asset_id": GOBTC,
                "denominating_asset_id": USDC,
                "price": 64000.5,
                "confidence": 1.0,
                "total_lockup": 0.11,
            },
            {
                "network_id": 0,
                "asset_id": 0,
                "denominating_asset_id": USDC,
                "price": 1.0,
                "confidence": 1.0,
                "total_lockup": 0.0,
            },
            {
                "network_id": 0,
                "asset_id": 7,
                "denominating_asset_id": USDC,
                "price": 0.0,
                "confidence": 0.0,
                "total_lockup": 0.0,
            },
        ]

    def test_api_vestige_prices_default_denomination_is_algo(self, latest):
        APIClient().get(URL, {"asset_ids": "5"})
        latest.assert_called_once_with([5], "algo")

    def test_api_vestige_prices_need_no_token_and_ignore_a_bad_one(self, latest):
        response = APIClient().get(
            URL, {"asset_ids": "5"}, HTTP_AUTHORIZATION="Bearer nonsense"
        )
        assert response.status_code == 200

    def test_api_vestige_prices_answer_any_origin(self, latest):
        for response in (
            APIClient().get(
                URL, {"asset_ids": "5"}, HTTP_ORIGIN="https://wallet.example"
            ),
            APIClient().get(URL),
        ):
            assert response["Access-Control-Allow-Origin"] == "*"

    def test_api_vestige_prices_too_many_assets(self, latest):
        most = ",".join(["5"] * VESTIGE_MAX_ASSETS)
        assert APIClient().get(URL, {"asset_ids": most}).status_code == 200
        response = APIClient().get(URL, {"asset_ids": most + ",5"})
        assert response.status_code == 406
        assert response.json() == {"detail": "Too many assets"}

    @pytest.mark.parametrize("name", ["network_id", "denominating_asset_id"])
    def test_api_vestige_prices_parameter_not_a_number(self, latest, name):
        response = APIClient().get(URL, {"asset_ids": "5", name: "abc"})
        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "int_parsing",
                    "loc": ["query", name],
                    "msg": "Input should be a valid integer, "
                    "unable to parse string as an integer",
                    "input": "abc",
                }
            ]
        }

    @pytest.mark.parametrize(
        "name,value,detail",
        [
            ("network_id", "1", "Unsupported network"),
            (
                "denominating_asset_id",
                "312769",
                "Unsupported denominating asset; use 0 (ALGO) or 31566704 (USDC)",
            ),
        ],
    )
    def test_api_vestige_prices_unsupported_values(self, latest, name, value, detail):
        response = APIClient().get(URL, {"asset_ids": "5", name: value})
        assert response.status_code == 400
        assert response.json() == {"detail": detail}
        latest.assert_not_called()

    @pytest.mark.parametrize("status_code", [None, 400, 403, 500])
    def test_api_vestige_prices_engine_failure_is_503_and_logged(
        self, mocker, status_code
    ):
        mocker.patch(
            "api.vestige.client.prices_latest",
            side_effect=BackendError("no", status_code=status_code),
        )
        logger = mocker.patch("api.vestige.logger")
        response = APIClient().get(URL, {"asset_ids": "5"})
        assert response.status_code == 503
        assert response.json() == {"detail": "Price service unavailable"}
        logger.error.assert_called_once()

    def test_api_vestige_prices_same_request_is_cached_briefly(self, latest, mocker):
        cached = mocker.spy(vestige.cache, "set")
        first = APIClient().get(URL, {"asset_ids": f"{GOBTC},0"})
        second = APIClient().get(URL, {"asset_ids": f"{GOBTC}, 0"})
        assert first.json() == second.json()
        latest.assert_called_once()
        assert [
            call.args[2]
            for call in cached.call_args_list
            if call.args[0].startswith("vestige:price:")
        ] == [VESTIGE_PRICE_CACHE_SECONDS]
        # another denomination or order is another answer
        APIClient().get(URL, {"asset_ids": f"0,{GOBTC}"})
        APIClient().get(URL, {"asset_ids": f"{GOBTC},0", "denominating_asset_id": USDC})
        assert latest.call_count == 3

    def test_api_vestige_prices_failure_is_not_cached(self, mocker):
        mocker.patch(
            "api.vestige.client.prices_latest",
            side_effect=[BackendError("no"), [entry(5, 2.0)]],
        )
        mocker.patch("api.vestige.logger")
        assert APIClient().get(URL, {"asset_ids": "5"}).status_code == 503
        assert APIClient().get(URL, {"asset_ids": "5"}).json()[0]["price"] == 2.0


class TestApiVestigeRateThrottle:
    """Testing class for :class:`api.vestige.VestigeRateThrottle`."""

    def test_api_vestige_throttle_rate_is_configured(self):
        assert VestigeRateThrottle().rate == "60/min"

    def test_api_vestige_throttle_headers_and_429(self, latest, mocker):
        mocker.patch.object(VestigeRateThrottle, "get_rate", return_value="2/min")
        client = APIClient()
        responses = [client.get(URL, {"asset_ids": "5"}) for _ in range(3)]
        assert [response.status_code for response in responses] == [200, 200, 429]
        assert [response["X-RateLimit-Limit"] for response in responses] == ["2"] * 3
        assert [response["X-RateLimit-Remaining"] for response in responses] == [
            "1",
            "0",
            "0",
        ]
        assert "Retry-After" in responses[2]
        assert responses[2]["Access-Control-Allow-Origin"] == "*"

    def test_api_vestige_throttle_counts_refused_requests_too(self, latest, mocker):
        mocker.patch.object(VestigeRateThrottle, "get_rate", return_value="1/min")
        client = APIClient()
        assert client.get(URL).status_code == 422
        assert client.get(URL, {"asset_ids": "5"}).status_code == 429

    def test_api_vestige_throttle_is_per_address_nginx_reports(self, latest, mocker):
        mocker.patch.object(VestigeRateThrottle, "get_rate", return_value="1/min")
        client = APIClient()
        first = {"HTTP_X_REAL_IP": "198.51.100.1"}
        assert client.get(URL, {"asset_ids": "5"}, **first).status_code == 200
        # a made-up X-Forwarded-For does not make a new caller
        assert (
            client.get(
                URL, {"asset_ids": "5"}, HTTP_X_FORWARDED_FOR="203.0.113.9", **first
            ).status_code
            == 429
        )
        assert (
            client.get(URL, {"asset_ids": "5"}, HTTP_X_REAL_IP="198.51.100.2").status_code
            == 200
        )

    def test_api_vestige_throttle_without_nginx_uses_the_peer_address(self, mocker):
        request = mocker.Mock(META={"REMOTE_ADDR": "192.0.2.7"})
        assert VestigeRateThrottle().get_cache_key(request, None) == (
            "throttle_vestige_192.0.2.7"
        )


class TestApiVestigeSchema:
    """Testing class for the Vestige-compatible endpoints in the OpenAPI schema."""

    def test_api_vestige_schema_lists_the_prices_without_a_token(self):
        response = APIClient().get("/api/v2/schema/", HTTP_ACCEPT="application/json")
        operation = response.json()["paths"]["/api/vestige/assets/price/"]["get"]
        assert operation["tags"] == ["Vestige compatibility"]
        assert "Moving from Vestige" in operation["description"]
        assert not operation.get("security")
        assert [parameter["name"] for parameter in operation["parameters"]] == [
            "asset_ids",
            "denominating_asset_id",
            "network_id",
        ]
