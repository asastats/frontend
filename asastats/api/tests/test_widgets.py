"""Testing module for :py:mod:`api.widgets` module."""

import pytest
from algosdk.constants import ADDRESS_LEN
from rest_framework.serializers import ValidationError

from api.widgets import (
    BearerAuth,
    bundle_and_addresses_from_path,
    widgets_api_view,
)
from utils.constants.apiv2 import BASE_API_URL
from utils.tests.fixtures import TEST_ADDRESS2, TEST_BUNDLE


class TestApiWidgetsBearerAuth:
    """Testing class for :py:class:`api.widgets.BearerAuth`."""

    def test_api_widgets_bearerauth_call_sets_authorization_header(self, mocker):
        mocked_settings = mocker.patch("api.widgets.settings")
        mocked_settings.WIDGETS_API_TOKEN = "secret-token"
        request = mocker.MagicMock(headers={})
        returned = BearerAuth()(request)
        assert returned == request
        assert request.headers["authorization"] == "Bearer secret-token"


class TestApiWidgetsFunctions:
    """Testing class for :py:mod:`api.widgets` functions."""

    # # bundle_and_addresses_from_path
    @pytest.mark.parametrize("url_path", [None, "", False, "0" * ADDRESS_LEN])
    def test_api_widgets_bundle_and_addresses_from_path_for_error(
        self, url_path, mocker
    ):
        mocked_bundle = mocker.patch("api.widgets.create_bundle")
        mocked_check = mocker.patch("api.widgets.check_bundle_addresses")
        with pytest.raises(ValidationError):
            bundle_and_addresses_from_path(url_path)
        mocked_bundle.assert_not_called()
        mocked_check.assert_not_called()

    def test_api_widgets_bundle_and_addresses_from_path_for_no_addresses(self, mocker):
        mocked_bundle = mocker.patch("api.widgets.create_bundle")
        mocker.patch("api.helpers.check_bundle_addresses", return_value="")
        with pytest.raises(ValidationError):
            bundle_and_addresses_from_path(TEST_BUNDLE)
        mocked_bundle.assert_not_called()

    def test_api_widgets_bundle_and_addresses_from_path_for_address_default_force(
        self, mocker
    ):
        mocker.patch("api.widgets.validate_bundle", return_value=TEST_ADDRESS2)
        mocked_bundle = mocker.patch("api.widgets.create_bundle")
        mocked_check = mocker.patch("api.widgets.check_bundle_addresses")
        url_path = TEST_ADDRESS2
        returned = bundle_and_addresses_from_path(url_path)
        assert returned == (mocked_bundle.return_value, TEST_ADDRESS2)
        mocked_bundle.assert_called_once_with(TEST_ADDRESS2)
        mocked_check.assert_not_called()

    def test_api_widgets_bundle_and_addresses_from_path_for_address_force_false(
        self, mocker
    ):
        mocker.patch("api.widgets.validate_bundle", return_value=TEST_ADDRESS2)
        mocked_bundle = mocker.patch("api.widgets.create_bundle")
        mocked_check = mocker.patch("api.widgets.check_bundle_addresses")
        url_path = TEST_ADDRESS2
        returned = bundle_and_addresses_from_path(url_path, force_bundle=False)
        assert returned == (TEST_ADDRESS2, TEST_ADDRESS2)
        mocked_bundle.assert_not_called()
        mocked_check.assert_not_called()

    @pytest.mark.django_db
    def test_api_widgets_bundle_and_addresses_from_path_for_bundle(self, mocker):
        mocked_validate = mocker.patch(
            "api.widgets.validate_bundle", return_value=TEST_BUNDLE
        )
        mocked_bundle = mocker.patch("api.widgets.create_bundle")
        addresses = mocker.MagicMock()
        mocked_check = mocker.patch(
            "api.widgets.check_bundle_addresses", return_value=addresses
        )
        url_path = TEST_BUNDLE
        returned = bundle_and_addresses_from_path(url_path)
        assert returned == (TEST_BUNDLE, addresses)
        mocked_validate.assert_called_once_with(TEST_BUNDLE)
        mocked_check.assert_called_once_with(TEST_BUNDLE)
        mocked_bundle.assert_not_called()

    # # widgets_api_view
    def test_api_widgets_widgets_api_view_without_filter(self, mocker):
        mocked_get = mocker.patch("api.widgets.requests.get")
        mocked_auth = mocker.patch("api.widgets.BearerAuth")
        returned = widgets_api_view("accounts")
        assert returned == mocked_get.return_value.json.return_value
        mocked_get.assert_called_once_with(
            f"{BASE_API_URL}accounts/", auth=mocked_auth.return_value
        )

    def test_api_widgets_widgets_api_view_with_filter(self, mocker):
        mocked_get = mocker.patch("api.widgets.requests.get")
        mocker.patch("api.widgets.BearerAuth")
        widgets_api_view("accounts", filter="active=1")
        mocked_get.assert_called_once()
        assert mocked_get.call_args.args[0] == f"{BASE_API_URL}accounts/?active=1"
