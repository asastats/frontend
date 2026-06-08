"""Testing module for :py:mod:`api.client` module."""

import pytest

from api.client import (
    BackendError,
    _headers,
    _request,
    download_export,
    engine_request,
    export_status,
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
        mocked_requests.request.assert_called_once()
        mocked_requests.request.assert_called_with(
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

    # # fetch_price
    def test_api_client_fetch_price_functionality(self, mocker):
        mocked_request = mocker.patch("api.client._request")
        mocked_request.return_value.json.return_value = {"price": 0.25}
        returned = fetch_price()
        assert returned == 0.25
        mocked_request.assert_called_once()
        mocked_request.assert_called_with("GET", "/api/v2/price/")

    # # fetch_serialized_account
    def test_api_client_fetch_serialized_account_without_addresses(self, mocker):
        value = API_EXAMPLE_ADDRESS1
        mocked_request = mocker.patch("api.client._request")
        returned = fetch_serialized_account(value)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once()
        mocked_request.assert_called_with(
            "GET", f"/api/v2/internal/accounts/{value}/", params=None
        )

    def test_api_client_fetch_serialized_account_with_addresses(self, mocker):
        value = API_EXAMPLE_BUNDLE1
        addresses = "FOO BAR"
        mocked_request = mocker.patch("api.client._request")
        returned = fetch_serialized_account(value, addresses)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once()
        mocked_request.assert_called_with(
            "GET",
            f"/api/v2/internal/accounts/{value}/",
            params={"addresses": addresses},
        )

    # # fetch_capabilities
    def test_api_client_fetch_capabilities_functionality(self, mocker):
        mocked_request = mocker.patch("api.client._request")
        returned = fetch_capabilities()
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once()
        mocked_request.assert_called_with("GET", "/api/v2/capabilities/")

    # # start_export
    def test_api_client_start_export_functionality(self, mocker):
        value = API_EXAMPLE_BUNDLE1
        addresses = "FOO BAR"
        mocked_request = mocker.patch("api.client._request")
        returned = start_export(value, addresses)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once()
        mocked_request.assert_called_with(
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
        mocked_request.assert_called_once()
        mocked_request.assert_called_with("GET", f"/api/v2/exports/{bundle}/status/")

    # # download_export
    def test_api_client_download_export_functionality(self, mocker):
        bundle = API_EXAMPLE_BUNDLE1
        mocked_request = mocker.patch("api.client._request")
        returned = download_export(bundle)
        assert returned == mocked_request.return_value.content
        mocked_request.assert_called_once()
        mocked_request.assert_called_with(
            "GET", f"/api/v2/exports/{bundle}/download/", stream=True
        )

    # # reset_export
    def test_api_client_reset_export_functionality(self, mocker):
        bundle = API_EXAMPLE_BUNDLE1
        mocked_request = mocker.patch("api.client._request")
        returned = reset_export(bundle)
        assert returned == mocked_request.return_value.json.return_value
        mocked_request.assert_called_once()
        mocked_request.assert_called_with("DELETE", f"/api/v2/exports/{bundle}/")


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
