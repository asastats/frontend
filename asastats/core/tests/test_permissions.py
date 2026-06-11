"""Testing module for :py:mod:`core.permissions` module."""

from unittest import mock

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from core.permissions import (
    BundleNamesRedirection,
    CanAccessApiMixin,
    CanAccessAuthorizeMixin,
    CanAddBundleNameMixin,
    CanUseBundleNamesMixin,
    ProfileRedirection,
    SubscribeRedirection,
)
from utils.constants.users import (
    ADJUST_BUNDLE_NAMES_SIZE_ERROR,
    SUBSCRIPTION_TIER_PERMISSIONS,
)

from .test_custom_views import BaseView


class TestCorePermissionBaseMixins:
    """Testing class for :py:mod:`core.permissions` base mixin classes."""

    # # SubscribeRedirection
    def test_subscriberedirection_is_subclass_of_userpassestestmixin(
        self,
    ):
        assert issubclass(SubscribeRedirection, UserPassesTestMixin)

    # # handle_no_permission
    def test_subscriberedirection_handle_no_permission_calls_and_returns_super(
        self,
    ):
        base = SubscribeRedirection()
        with mock.patch(
            "core.permissions.UserPassesTestMixin.handle_no_permission"
        ) as mocked_super:
            returned = base.handle_no_permission()
            assert returned == mocked_super.return_value
            mocked_super.assert_called_once_with()

    def test_subscriberedirection_handle_no_permission_redirects_on_exception(
        self, mocker
    ):
        mocked_redirect = mocker.patch("core.permissions.redirect")
        base = SubscribeRedirection()
        with mock.patch(
            "core.permissions.UserPassesTestMixin.handle_no_permission"
        ) as mocked_super:
            mocked_super.side_effect = PermissionDenied("", "", 0)
            returned = base.handle_no_permission()
        assert returned == mocked_redirect.return_value
        mocked_redirect.assert_called_once_with("subscriptions")

    # # BundleNamesRedirection
    def test_bundlenamesredirection_is_subclass_of_userpassestestmixin(
        self,
    ):
        assert issubclass(BundleNamesRedirection, UserPassesTestMixin)

    # # handle_no_permission
    def test_bundlenamesredirection_handle_no_permission_calls_and_returns_super(
        self,
    ):
        base = BundleNamesRedirection()
        with mock.patch(
            "core.permissions.UserPassesTestMixin.handle_no_permission"
        ) as mocked_super:
            returned = base.handle_no_permission()
            assert returned == mocked_super.return_value
            mocked_super.assert_called_once_with()

    # # ProfileRedirection
    def test_profileredirection_is_subclass_of_userpassestestmixin(
        self,
    ):
        assert issubclass(ProfileRedirection, UserPassesTestMixin)

    # # handle_no_permission
    def test_profileredirection_handle_no_permission_calls_and_returns_super(
        self,
    ):
        base = ProfileRedirection()
        with mock.patch(
            "core.permissions.UserPassesTestMixin.handle_no_permission"
        ) as mocked_super:
            returned = base.handle_no_permission()
            assert returned == mocked_super.return_value
            mocked_super.assert_called_once_with()

    def test_profileredirection_handle_no_permission_redirects_on_exception(
        self, mocker
    ):
        mocked_redirect = mocker.patch("core.permissions.redirect")
        base = ProfileRedirection()
        with mock.patch(
            "core.permissions.UserPassesTestMixin.handle_no_permission"
        ) as mocked_super:
            mocked_super.side_effect = PermissionDenied("", "", 0)
            returned = base.handle_no_permission()
        assert returned == mocked_redirect.return_value
        mocked_redirect.assert_called_once_with("profile")


class TestCorePermissionUserMixins(BaseView):
    """Testing class for :py:mod:`core.permissions` user related base mixin methods."""

    # # BundleNamesRedirection
    # # handle_no_permission
    def test_bundlenamesredirection_handle_no_permission_redirects_to_home(
        self, mocker
    ):
        mocked_redirect = mocker.patch("core.permissions.redirect")
        view = BundleNamesRedirection()
        self.request.user = mocker.MagicMock()
        self.request.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        view = self.setup_view(view, self.request)
        with (
            mock.patch(
                "core.permissions.UserPassesTestMixin.handle_no_permission"
            ) as mocked_super,
            mock.patch("core.permissions.messages") as mocked_messages,
            mock.patch("core.permissions.mark_safe") as mocked_safe,
        ):
            mocked_super.side_effect = PermissionDenied("", "", 0)
            returned = view.handle_no_permission()
            mocked_safe.assert_called_once_with(ADJUST_BUNDLE_NAMES_SIZE_ERROR)
            mocked_messages.error.assert_called_once_with(
                self.request, mocked_safe.return_value
            )
        assert returned == mocked_redirect.return_value
        mocked_redirect.assert_called_once_with("home")

    def test_bundlenamesredirection_handle_no_permission_redirects_to_subscriptions(
        self, mocker
    ):
        mocked_redirect = mocker.patch("core.permissions.redirect")
        view = BundleNamesRedirection()
        self.request.user = mocker.MagicMock()
        self.request.user.profile.permission = (
            SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1
        )
        view = self.setup_view(view, self.request)
        with (
            mock.patch(
                "core.permissions.UserPassesTestMixin.handle_no_permission"
            ) as mocked_super,
            mock.patch("core.permissions.messages") as mocked_messages,
            mock.patch("core.permissions.mark_safe") as mocked_safe,
        ):
            mocked_super.side_effect = PermissionDenied("", "", 0)
            returned = view.handle_no_permission()
            mocked_safe.assert_not_called()
            mocked_messages.assert_not_called()
        assert returned == mocked_redirect.return_value
        mocked_redirect.assert_called_once_with("subscriptions")


class TestCorePermissionMixins:
    """Testing class for :py:mod:`core.permissions` mixin classes."""

    # # CanAccessApiMixin
    def test_core_permissions_canaccessapimixin_is_subclass_of_subscriberedirection(
        self,
    ):
        assert issubclass(CanAccessApiMixin, SubscribeRedirection)

    # # test_func
    def test_core_permissions_canaccessapimixin_test_func_calls_can_access_api(
        self, mocker
    ):
        mixin = CanAccessApiMixin()
        mixin.request = mocker.MagicMock()
        mixin.test_func()
        mixin.request.user.profile.can_access_api.assert_called_once_with()

    # # CanAccessAuthorizeMixin
    def test_core_permissions_canaccessauthorizemixin_is_subclass_of_profileredirection(
        self,
    ):
        assert issubclass(CanAccessAuthorizeMixin, ProfileRedirection)

    # # test_func
    def test_core_permissions_canaccessauthorizemixin_test_func_calls_can_access_auth(
        self, mocker
    ):
        mixin = CanAccessAuthorizeMixin()
        mixin.request = mocker.MagicMock()
        mixin.test_func()
        mixin.request.user.profile.can_access_authorize.assert_called_once_with()

    # # CanAddBundleNameMixin
    def test_core_permissions_canaddbundlenamemixin_is_subclass_of_subscriberedirection(
        self,
    ):
        assert issubclass(CanAddBundleNameMixin, SubscribeRedirection)

    # # test_func
    def test_core_permissions_canaddbundlenamemixin_test_func_calls_can_add(
        self, mocker
    ):
        mixin = CanAddBundleNameMixin()
        mixin.request = mocker.MagicMock()
        mixin.test_func()
        mixin.request.user.profile.can_add_bundle_name.assert_called_once_with()

    # # CanUseBundleNamesMixin
    def test_core_permissions_canusebundlenamesmixin_is_subclass_of_homeredirection(
        self,
    ):
        assert issubclass(CanUseBundleNamesMixin, BundleNamesRedirection)

    # # test_func
    def test_core_permissions_canusebundlenamesmixin_test_func_calls_can_use_bundles(
        self, mocker
    ):
        mixin = CanUseBundleNamesMixin()
        mixin.request = mocker.MagicMock()
        mixin.test_func()
        mixin.request.user.profile.can_use_bundle_names.assert_called_once_with()
