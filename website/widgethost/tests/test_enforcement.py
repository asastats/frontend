"""Testing module for :py:mod:`widgethost.enforcement` module."""

from widgethost.enforcement import WidgetAccessMixin


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

    def test_widgethost_enforcement_widget_access_mixin_denies_on_callback(
        self, mocker
    ):
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
