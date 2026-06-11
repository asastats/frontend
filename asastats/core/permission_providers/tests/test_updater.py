"""Testing module for :py:mod:`core.permission_providers.updater` module."""

import core.permission_providers.updater as updater
from core.permission_providers.updater import (
    _check_interval_passed,
    _exit_gracefully,
    _refresh_permissions,
)

MODULE = "core.permission_providers.updater"


class TestCorePermissionProvidersUpdaterRefreshPermissions:
    """Testing class for :py:func:`...updater._refresh_permissions`."""

    def test_core_permission_providers_updater_refresh_permissions_calls_provider(
        self, mocker
    ):
        provider = mocker.patch(f"{MODULE}.get_permission_provider").return_value
        _refresh_permissions()
        provider.refresh.assert_called_once_with()


class TestCorePermissionProvidersUpdaterCheckIntervalPassed:
    """Testing class for :py:func:`...updater._check_interval_passed`."""

    def test_core_permission_providers_updater_check_interval_passed_without_last(
        self, mocker
    ):
        clock = mocker.patch(f"{MODULE}.datetime")
        clock.now.return_value.timestamp.return_value = 1234.0
        pause = mocker.patch(f"{MODULE}.pause")
        assert _check_interval_passed(None) == 1234.0
        pause.assert_not_called()

    def test_core_permission_providers_updater_check_interval_passed_after_ttl(
        self, mocker
    ):
        clock = mocker.patch(f"{MODULE}.datetime")
        clock.now.return_value.timestamp.return_value = 5000.0
        mocker.patch(f"{MODULE}.PERMISSIONS_TTL", 10)
        pause = mocker.patch(f"{MODULE}.pause")
        assert _check_interval_passed(100.0) == 5000.0
        pause.assert_not_called()

    def test_core_permission_providers_updater_check_interval_passed_waits(
        self, mocker
    ):
        clock = mocker.patch(f"{MODULE}.datetime")
        clock.now.return_value.timestamp.side_effect = [55.0, 5000.0]
        mocker.patch(f"{MODULE}.PERMISSIONS_TTL", 10)
        pause = mocker.patch(f"{MODULE}.pause")
        assert _check_interval_passed(50.0) == 5000.0
        assert pause.call_count == 1


class TestCorePermissionProvidersUpdaterExitGracefully:
    """Testing class for :py:func:`...updater._exit_gracefully`."""

    def test_core_permission_providers_updater_exit_gracefully_sets_signal(self):
        updater.exit_signal = False
        _exit_gracefully()
        assert updater.exit_signal is True
        updater.exit_signal = False
