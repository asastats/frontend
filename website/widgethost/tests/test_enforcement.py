"""Testing module for :py:mod:`widgethost.enforcement` module."""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from widgethost.enforcement import WidgetAccessMixin

INVALID = "IEDY3UI3X7SK7HCDRDRCRSULHWOT4Y6BNEGZGBJ3OD33LEBIYZS35Q6ZQQ"


class TestWidgethostEnforcementWidgetAccessMixin:
    """Testing class for :py:class:`widgethost.enforcement.WidgetAccessMixin`."""

    def _mixin(self, mocker, permission=10, authenticated=True):
        mixin = WidgetAccessMixin()
        mixin.manifest = mocker.MagicMock(required_permission=5)
        mixin.request = mocker.MagicMock()
        mixin.request.user.is_authenticated = authenticated
        mixin.request.user.profile.permission = permission
        return mixin

    def test_widgethost_enforcement_widget_access_mixin_allows(self, mocker):
        mixin = self._mixin(mocker)
        mocker.patch("widgethost.enforcement.can_access", return_value=True)
        assert mixin.manifest_test_func(2) is True

    def test_widgethost_enforcement_widget_access_mixin_denies_on_callback(self, mocker):
        mixin = self._mixin(mocker)
        mocker.patch("widgethost.enforcement.can_access", return_value=False)
        assert mixin.manifest_test_func(2) is False

    def test_widgethost_enforcement_widget_access_mixin_denies_anonymous(self, mocker):
        mixin = self._mixin(mocker, authenticated=False)
        mocker.patch("widgethost.enforcement.can_access", return_value=True)
        assert mixin.manifest_test_func(2) is False

    def test_widgethost_enforcement_widget_access_mixin_access_callback(self, mocker):
        mixin = WidgetAccessMixin()
        mixin.manifest = mocker.MagicMock(required_permission=[{"max_addresses": 1}])
        mocked = mocker.patch("widgethost.enforcement.can_access", return_value=True)
        profile = mocker.MagicMock(permission=9)
        assert mixin._access_callback(profile, 3) is True
        mocked.assert_called_once_with(9, mixin.manifest.required_permission, 3)


class TestWidgethostEnforcementInvalidPath:
    """An invalid URL value goes back to the index with its error, not a 500."""

    def test_widgethost_enforcement_test_func_turns_validation_error_into_false(
        self, mocker
    ):
        mixin = WidgetAccessMixin()
        mixin.test_func = mocker.MagicMock(side_effect=ValidationError("Invalid!"))
        assert mixin.get_test_func()() is False
        assert mixin.invalid_path == "Invalid!"

    def test_widgethost_enforcement_test_func_for_api_validation_error(self, mocker):
        from rest_framework.exceptions import ValidationError as ApiValidationError

        mixin = WidgetAccessMixin()
        mixin.test_func = mocker.MagicMock(side_effect=ApiValidationError("Bad!"))
        assert mixin.get_test_func()() is False
        assert mixin.invalid_path == "Bad!"

    def test_widgethost_enforcement_test_func_passes_through(self, mocker):
        mixin = WidgetAccessMixin()
        mixin.test_func = mocker.MagicMock(return_value=True)
        assert mixin.get_test_func()() is True
        assert mixin.invalid_path is None

    def test_widgethost_enforcement_handle_no_permission_for_invalid_path(self, mocker):
        mixin = WidgetAccessMixin()
        mixin.request = mocker.MagicMock()
        mixin.invalid_path = "Invalid!"
        error = mocker.patch("widgethost.enforcement.messages.error")
        response = mixin.handle_no_permission()
        error.assert_called_once_with(mixin.request, "Invalid!")
        assert response.url == "/"

    def test_widgethost_enforcement_handle_no_permission_functionality(self, mocker):
        mixin = WidgetAccessMixin()
        mixin.request = mocker.MagicMock()
        mixin.invalid_path = None
        error = mocker.patch("widgethost.enforcement.messages.error")
        with pytest.raises(PermissionDenied):
            mixin.handle_no_permission()
        error.assert_not_called()

    @pytest.mark.parametrize("prefix", ["historic", "pnl"])
    def test_widgethost_enforcement_invalid_address_in_widget_url(self, client, prefix):
        response = client.get(f"/widgets/{prefix}/{INVALID}", follow=True)
        assert response.redirect_chain[-1] == ("/", 302)
        assert "Invalid Algorand address!" in response.content.decode()

    @pytest.mark.django_db
    @pytest.mark.parametrize("prefix", ["historic", "pnl"])
    def test_widgethost_enforcement_unknown_bundle_in_widget_url_signed_in(
        self, client, django_user_model, mocker, prefix
    ):
        mocker.patch("api.helpers.check_bundle_addresses", return_value="")
        user = django_user_model.objects.create_user(username="reader", password="pw")
        client.force_login(user)
        response = client.get(f"/widgets/{prefix}/{'B' * 40}")
        assert response.status_code == 302
        assert response.url == "/"
