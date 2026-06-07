"""Module containing core app mixin classes for subscription permissions."""

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.safestring import mark_safe

from utils.constants.users import (
    ADJUST_BUNDLE_NAMES_SIZE_ERROR,
    SUBSCRIPTION_TIER_PERMISSIONS,
)


class BundleNamesRedirection(UserPassesTestMixin):
    """Base class redirecting to home when access is denied."""

    def handle_no_permission(self):
        """Calls super method and redirect to subscribe page on exception."""
        try:
            return super().handle_no_permission()

        except PermissionDenied:
            if (
                self.request.user.profile.permission
                >= SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
            ):
                messages.error(self.request, mark_safe(ADJUST_BUNDLE_NAMES_SIZE_ERROR))
                return redirect("home")

            return redirect("subscriptions")


class ProfileRedirection(UserPassesTestMixin):
    """Base class redirecting to profile page when access is denied."""

    def handle_no_permission(self):
        """Calls super method and redirect to profile page on exception."""
        try:
            return super().handle_no_permission()

        except PermissionDenied:
            return redirect("profile")


class SubscribeRedirection(UserPassesTestMixin):
    """Base class redirecting to subscribe when access is denied."""

    def handle_no_permission(self):
        """Calls super method and redirect to subscribe page on exception."""
        try:
            return super().handle_no_permission()

        except PermissionDenied:
            return redirect("subscriptions")


class CanAccessApiMixin(SubscribeRedirection):
    """Class with method for determining if user is allowed to access API."""

    def test_func(self):
        """Return True if user is allowed to create another bundle name.

        :return: Boolean
        """
        return self.request.user.profile.can_access_api()


class CanAccessAuthorizeMixin(ProfileRedirection):
    """Class with method for determining if user is allowed to access API."""

    def test_func(self):
        """Return True if user is allowed to create another bundle name.

        :return: Boolean
        """
        return self.request.user.profile.can_access_authorize()


class CanAddBundleNameMixin(SubscribeRedirection):
    """Class with method for determining if user can add a bundle name."""

    def test_func(self):
        """Return True if user is allowed to create another bundle name.

        :return: Boolean
        """
        return self.request.user.profile.can_add_bundle_name()


class CanUseBundleNamesMixin(BundleNamesRedirection):
    """Class with method for determining if user can use created bundle names."""

    def test_func(self):
        """Return True if user is allowed to use created bundle names.

        :return: Boolean
        """
        return self.request.user.profile.can_use_bundle_names()
