"""Testing module for :py:mod:`api.permissions` module."""

import pytest
from rest_framework.permissions import BasePermission

from api.permissions import CanAccessApiPermission


class TestCanAccessApiPermission:
    """Testing class for :class:`api.permissions.CanAccessApiPermission`."""

    # # CanAccessApiPermission
    def test_api_permissions_canaccessapipermission_issubclass_of_basepermission(self):
        assert issubclass(CanAccessApiPermission, BasePermission)

    def test_api_permissions_canaccessapipermission_has_permission_returns_true(
        self, mocker
    ):
        permission = CanAccessApiPermission()
        assert permission.has_permission(mocker.MagicMock(), mocker.MagicMock()) is True

    @pytest.mark.skip(reason="Still awaiting implementation.")
    def test_api_permissions_canaccessapipermission_has_permission_for_true(
        self, mocker
    ):
        request = mocker.MagicMock()
        request.user.profile.can_access_api.return_value = True
        permission = CanAccessApiPermission()
        assert permission.has_permission(request, mocker.MagicMock()) is True
        request.user.profile.can_access_api.assert_called_once()
        request.user.profile.can_access_api.assert_called_with()

    @pytest.mark.skip(reason="Still awaiting implementation.")
    def test_api_permissions_canaccessapipermission_has_permission_for_false(
        self, mocker
    ):
        request = mocker.MagicMock()
        request.user.profile.can_access_api.return_value = False
        permission = CanAccessApiPermission()
        assert permission.has_permission(request, mocker.MagicMock()) is False
        request.user.profile.can_access_api.assert_called_once()
        request.user.profile.can_access_api.assert_called_with()
