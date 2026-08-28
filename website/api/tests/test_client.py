"""Testing module for :py:mod:`api.client` module."""

import pytest

from api.client import (
    BackendError,
    _headers,
    _request,
    download_export,
    engine_request,
    export_status,
    fetch_account_holdings,
    fetch_asset_matches,
    fetch_capabilities,
    fetch_price,
    fetch_serialized_account,
    reset_export,
    start_export,
)
from api.data import API_EXAMPLE_ADDRESS1, API_EXAMPLE_BUNDLE1


class TestApiClientFunctions:
    """Testing class for :py:mod:`api.client` functions."""

    # # _headers
    def test_api_client_headers_functionality(self, mocker):
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_KEY = "secret-key"
        assert _headers() == {"Authorization": "Bearer secret-key"}

    # # _request
    def test_api_client_request_functionality(self, mocker):
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_URL = "https://api.test"
        mocked_settings.ASASTATS_API_TIMEOUT = 30
        mocked_headers = mocker.patch("api.client._headers")
        mocked_requests = mocker.patch("api.client.requests")
        mocked_requests.request.return_value.status_code = 200
        returned = _request("GET", "/path/")
        assert returned == mocked_requests.request.return_value
        mocked_requests.request.assert_called_once_with(
            "GET",
            "https://api.test/path/",
            headers=mocked_headers.return_value,
            timeout=30,
        )

    def test_api_client_request_passes_extra_kwargs(self, mocker):
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_URL = "https://api.test"
        mocked_settings.ASASTATS_API_TIMEOUT = 30
        mocker.patch("api.client._headers")
        mocked_requests = mocker.patch("api.client.requests")
        mocked_requests.request.return_value.status_code = 200
        params = {"addresses": "foo bar"}
        _request("GET", "/path/", params=params)
        assert mocked_requests.request.call_args.kwargs["params"] == params

    def test_api_client_request_raises_backenderror_on_error_status(self, mocker):
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_URL = "https://api.test"
        mocked_settings.ASASTATS_API_TIMEOUT = 30
        mocker.patch("api.client._headers")
        mocked_requests = mocker.patch("api.client.requests")
        mocked_requests.request.return_value.status_code = 404
        mocked_requests.request.return_value.text = "missing"
        with pytest.raises(BackendError):
            _request("GET", "/path/")

    def test_api_client_request_carries_the_backends_own_explanation(self, mocker):
        """The refusal a caller can pass on, rather than a 500.

        The engine's router endpoints depend on this: a restricted deployment
        answers 503 with a sentence explaining *why* no group can be built, and
        that sentence is the only thing a reader could act on.
        """
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_URL = "https://api.test"
        mocked_settings.ASASTATS_API_TIMEOUT = 30
        mocker.patch("api.client._headers")
        mocked_requests = mocker.patch("api.client.requests")
        response = mocked_requests.request.return_value
        response.status_code = 503
        response.text = '{"detail": "this deployment may not build groups"}'
        response.json.return_value = {"detail": "this deployment may not build groups"}

        with pytest.raises(BackendError) as raised:
            _request("GET", "/router/quote/")

        assert raised.value.status_code == 503
        assert raised.value.detail == "this deployment may not build groups"

    def test_api_client_request_survives_an_error_body_that_is_not_json(self, mocker):
        """An error page, a proxy's plain text, a truncated response.

        The backend is not the only thing that can answer: a gateway between
        here and it returns HTML, and `resp.json()` then raises. Letting that
        propagate would replace the backend's status - which the caller can act
        on - with a ValueError from inside the client, so the status and the
        response text survive and only the structured detail is dropped.
        """
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_URL = "https://api.test"
        mocked_settings.ASASTATS_API_TIMEOUT = 30
        mocker.patch("api.client._headers")
        mocked_requests = mocker.patch("api.client.requests")
        response = mocked_requests.request.return_value
        response.status_code = 502
        response.text = "<html><body>502 Bad Gateway</body></html>"
        response.json.side_effect = ValueError("not json")

        with pytest.raises(BackendError) as raised:
            _request("GET", "/path/")

        assert raised.value.status_code == 502
        assert raised.value.detail is None
        assert "502 Bad Gateway" in str(raised.value)

    def test_api_client_request_truncates_a_long_error_body(self, mocker):
        """A gateway's error page can be megabytes; a log line should not be.

        Pinned because the slice is the only thing standing between an
        exception message and the whole of whatever answered.
        """
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_URL = "https://api.test"
        mocked_settings.ASASTATS_API_TIMEOUT = 30
        mocker.patch("api.client._headers")
        mocked_requests = mocker.patch("api.client.requests")
        response = mocked_requests.request.return_value
        response.status_code = 500
        response.text = "x" * 5000
        response.json.side_effect = ValueError("not json")

        with pytest.raises(BackendError) as raised:
            _request("GET", "/path/")

        assert len(str(raised.value)) < 300

    def test_api_client_request_refuses_a_relative_path(self, mocker):
        """A path without a leading slash is refused before it is sent.

        The URL is built by concatenation, so ``router/quote/`` produced
        ``http://host:8001router/quote/`` - a host that does not exist and a
        request that never reached the engine. The asastats widget shipped with
        exactly that. Refused here rather than left to `requests` to reject,
        because InvalidURL names neither the caller nor the bad path.
        """
        mocked_settings = mocker.patch("api.client.settings")
        mocked_settings.ASASTATS_API_URL = "https://api.test"
        mocked_requests = mocker.patch("api.client.requests")

        with pytest.raises(BackendError) as raised:
            _request("GET", "router/quote/")

        assert "must start with '/'" in str(raised.value)
        assert not mocked_requests.request.called

    # # fetch_price
    def test_api_client_fetch_price_functionality(self, mocker):
        mocked_request = mocker.patch("api.client._request")
        mocked_request.return_value.json.return_value = {"price": 0.25}
        returned = fetch_price()
        assert returned == 0.25
        mocked_request.assert_called_once_with("GET", "/api/v2/price/")

    # # fetch_serialized_account
    def test_api_client_fetch_serialized_account_without_addresses(self, mocker):
        value = API_EXAMPLE_ADDRESS1
        mocked_request = mocker.patch("api.client._request")
        returned = fetch_serialized_account(value)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once_with(
            "GET", f"/api/v2/internal/accounts/{value}/", params=None
        )

    def test_api_client_fetch_serialized_account_with_addresses(self, mocker):
        value = API_EXAMPLE_BUNDLE1
        addresses = "FOO BAR"
        mocked_request = mocker.patch("api.client._request")
        returned = fetch_serialized_account(value, addresses)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once_with(
            "GET",
            f"/api/v2/internal/accounts/{value}/",
            params={"addresses": addresses},
        )

    # # fetch_account_holdings
    def test_api_client_fetch_account_holdings_functionality(self, mocker):
        mocked_engine = mocker.patch("api.client.engine_request")
        scopes = ["account:holdings", "assets:lookup"]
        returned = fetch_account_holdings("ADDRESS", scopes)
        assert returned == mocked_engine.return_value.json.return_value
        mocked_engine.assert_called_once_with(
            "account:holdings",
            "GET",
            "/api/v2/internal/accounts/ADDRESS/holdings",
            scopes,
        )

    # # fetch_asset_matches
    def test_api_client_fetch_asset_matches_functionality(self, mocker):
        mocked_engine = mocker.patch("api.client.engine_request")
        scopes = ["account:holdings", "assets:lookup"]
        returned = fetch_asset_matches("usdc", scopes)
        assert returned == mocked_engine.return_value.json.return_value
        mocked_engine.assert_called_once_with(
            "assets:lookup",
            "GET",
            "/api/v2/internal/assets",
            scopes,
            params={"q": "usdc"},
        )

    # # fetch_capabilities
    def test_api_client_fetch_capabilities_functionality(self, mocker):
        mocked_request = mocker.patch("api.client._request")
        returned = fetch_capabilities()
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once_with("GET", "/api/v2/capabilities/")

    # # start_export
    def test_api_client_start_export_functionality(self, mocker):
        value = API_EXAMPLE_BUNDLE1
        addresses = "FOO BAR"
        mocked_request = mocker.patch("api.client._request")
        returned = start_export(value, addresses)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once_with(
            "POST",
            "/api/v2/exports/",
            json={"bundle": value, "addresses": addresses},
        )

    # # export_status
    def test_api_client_export_status_functionality(self, mocker):
        bundle = API_EXAMPLE_BUNDLE1
        mocked_request = mocker.patch("api.client._request")
        returned = export_status(bundle)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once_with(
            "GET", f"/api/v2/exports/{bundle}/status/"
        )

    # # download_export
    def test_api_client_download_export_functionality(self, mocker):
        bundle = API_EXAMPLE_BUNDLE1
        mocked_request = mocker.patch("api.client._request")
        returned = download_export(bundle)
        assert returned == mocked_request.return_value.content
        mocked_request.assert_called_once_with(
            "GET", f"/api/v2/exports/{bundle}/download/", stream=True
        )

    # # reset_export
    def test_api_client_reset_export_functionality(self, mocker):
        bundle = API_EXAMPLE_BUNDLE1
        mocked_request = mocker.patch("api.client._request")
        returned = reset_export(bundle)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once_with("DELETE", f"/api/v2/exports/{bundle}/")


class TestApiClientEngineRequest:
    """Testing class for :py:func:`api.client.engine_request`."""

    def test_api_client_engine_request_for_undeclared_scope(self, mocker):
        mocked = mocker.patch("api.client._request")
        with pytest.raises(BackendError):
            engine_request("historic:evaluate", "POST", "/p/", ["historic:process"])
        mocked.assert_not_called()

    def test_api_client_engine_request_delegates_for_declared_scope(self, mocker):
        mocked = mocker.patch("api.client._request")
        returned = engine_request(
            "historic:evaluate", "POST", "/p/", ["historic:evaluate"], json={"a": 1}
        )
        assert returned == mocked.return_value
        mocked.assert_called_once_with("POST", "/p/", json={"a": 1})
