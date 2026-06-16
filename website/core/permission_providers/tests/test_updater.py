"""Testing module for :py:mod:`core.permission_providers.updater` module."""

import signal
from unittest import mock

import core.permission_providers.updater as updater
from core.permission_providers.updater import (
    _check_interval_passed,
    _exit_gracefully,
    _initializer,
    _refresh_permissions,
    run_permissions_update,
)
from utils.constants.core import PERMISSIONS_TTL, QUARTER

MODULE = "core.permission_providers.updater"


class TestCorePermissionProvidersUpdaterProcessFunctions:
    """Testing class for :py:mod:`core.permission_providers.updater` process funcs."""

    def test_core_permission_providers_updater_refresh_permissions_calls_refresh(
        self, mocker
    ):
        provider = mocker.patch(f"{MODULE}.get_permission_provider").return_value
        _refresh_permissions()
        provider.refresh.assert_called_once_with()


class TestCorePermissionProvidersUpdaterHelperFunctions:
    """Testing class for :py:mod:`core.permission_providers.updater` main functions."""

    def test_core_permission_providers_updater_check_interval_passed_none_timestamp(
        self, mocker
    ):
        last_timestamp = None
        mocked_pause = mocker.patch(f"{MODULE}.pause")
        with mock.patch(f"{MODULE}.datetime") as mocked_datetime:
            returned = _check_interval_passed(last_timestamp)
        assert returned == mocked_datetime.now.return_value.timestamp.return_value
        mocked_pause.assert_not_called()

    def test_core_permission_providers_updater_check_interval_passed_functionality(
        self, mocker
    ):
        last_timestamp = 123456789
        mocked_pause = mocker.patch(f"{MODULE}.pause")
        with mock.patch(f"{MODULE}.datetime") as mocked_datetime:
            mocked_datetime.now.return_value.timestamp.side_effect = [
                last_timestamp,
                last_timestamp + 1,
                last_timestamp + PERMISSIONS_TTL + 1,
            ]
            returned = _check_interval_passed(last_timestamp)
        assert returned == last_timestamp + PERMISSIONS_TTL + 1
        calls = [mocker.call(QUARTER)]
        mocked_pause.assert_has_calls(calls, any_order=True)
        assert mocked_pause.call_count == 2

    def test_core_permission_providers_updater_exit_gracefully_functionality(self):
        assert updater.exit_signal is False
        _exit_gracefully()
        assert updater.exit_signal is True

    def test_core_permission_providers_updater_initializer_functionality(self, mocker):
        mocked_logger = mocker.patch(f"{MODULE}.create_multiprocess_logger")
        with mock.patch(f"{MODULE}.os.getpid") as mocked_pid:
            _initializer()
            mocked_pid.assert_called_once_with()
        assert updater.logger == mocked_logger.return_value
        mocked_logger.assert_called_once_with(mocked_pid.return_value)


class TestCorePermissionProvidersUpdaterRunPermissionsUpdate:
    """Testing class for :py:func:`...updater.run_permissions_update`."""

    def _setup_single_cycle(self, mocker):
        """Patch a single ``run_permissions_update`` cycle and stop the loop.

        :param mocker: pytest-mock fixture
        :type mocker: :class:`pytest_mock.MockerFixture`
        :var pool: mocked multiprocessing pool context value
        :type pool: :class:`unittest.mock.MagicMock`
        :return: two-tuple of the pool mock and the logger mock
        """
        updater.exit_signal = False
        mocker.patch(f"{MODULE}.signal")
        mocked_time = mocker.patch(f"{MODULE}.time")
        mocked_time.time.side_effect = [0.0, 0.0]
        mocked_logger = mocker.patch(f"{MODULE}.create_multiprocess_logger")
        mocked_pool_class = mocker.patch(f"{MODULE}.Pool")
        pool = mocked_pool_class.return_value.__enter__.return_value

        def stop(*args, **kwargs):
            """Set the module exit signal so the loop terminates."""
            updater.exit_signal = True

        pool.apply.side_effect = stop
        return pool, mocked_logger.return_value

    def test_core_permission_providers_updater_run_permissions_update_exits_on_signal(
        self, mocker
    ):
        with (
            mock.patch.object(updater, "exit_signal", True),
            mock.patch(f"{MODULE}.create_multiprocess_logger") as mocked_logger,
            mock.patch(f"{MODULE}.Pool") as mocked_pool,
            mock.patch(f"{MODULE}.signal.signal") as mocked_signal,
            mock.patch(f"{MODULE}.os.getpid") as mocked_pid,
        ):
            mock_close, mock_join, mock_apply = (
                mocker.MagicMock(),
                mocker.MagicMock(),
                mocker.MagicMock(),
            )
            mocked_pool.return_value.__enter__.return_value.close = mock_close
            mocked_pool.return_value.__enter__.return_value.join = mock_join
            mocked_pool.return_value.__enter__.return_value.apply = mock_apply
            run_permissions_update()
            calls = [
                mocker.call(signal.SIGINT, _exit_gracefully),
                mocker.call(signal.SIGTERM, _exit_gracefully),
            ]
            mocked_signal.assert_has_calls(calls, any_order=True)
            assert mocked_signal.call_count == 2
            mocked_logger.assert_called_once_with(
                mocked_pid.return_value, prefix="permissions"
            )
            mocked_pool.assert_called_once_with(
                processes=1, initializer=updater._initializer
            )
            mock_close.assert_called_once_with()
            mock_join.assert_called_once_with()
            mock_apply.assert_not_called()

    def test_core_permission_providers_updater_run_permissions_update_doesnt_log(
        self, mocker
    ):
        with (
            mock.patch.object(updater, "exit_signal", False),
            mock.patch(f"{MODULE}.create_multiprocess_logger") as mocked_logger,
            mock.patch(f"{MODULE}.Pool") as mocked_pool,
            mock.patch(f"{MODULE}.signal.signal"),
            mock.patch(f"{MODULE}.os.getpid"),
            mock.patch(f"{MODULE}.time.time", side_effect=[1, 10]),
        ):
            mock_apply, mock_async = mocker.MagicMock(), mocker.MagicMock()
            mocked_pool.return_value.__enter__.return_value.apply = mock_apply
            mocked_pool.return_value.__enter__.return_value.apply_async = mock_async
            mock_async.return_value.wait.side_effect = _exit_gracefully
            run_permissions_update()
            mock_apply.assert_called_once()
            mock_apply.assert_called_once_with(_check_interval_passed, [None])
            mock_async.return_value.get.assert_called_once()
            mock_async.return_value.get.assert_called_once_with()
            mock_async.return_value.wait.assert_called_once()
            mock_async.return_value.wait.assert_called_once_with()
            mocked_logger.return_value.warning.assert_not_called()

    def test_core_permission_providers_updater_run_permissions_update_logs_timeout(
        self, mocker
    ):
        with (
            mock.patch.object(updater, "exit_signal", False),
            mock.patch(f"{MODULE}.create_multiprocess_logger") as mocked_logger,
            mock.patch(f"{MODULE}.Pool") as mocked_pool,
            mock.patch(f"{MODULE}.signal.signal"),
            mock.patch(f"{MODULE}.os.getpid"),
            mock.patch(f"{MODULE}.time.time", side_effect=[100, 110, 120, 200]),
        ):
            mock_apply, mock_async = mocker.MagicMock(), mocker.MagicMock()
            mocked_pool.return_value.__enter__.return_value.apply = mock_apply
            mocked_pool.return_value.__enter__.return_value.apply_async = mock_async
            mocked_logger.return_value.warning.side_effect = _exit_gracefully
            mock_apply.return_value = 150
            run_permissions_update()
            calls = [
                mocker.call(_check_interval_passed, [None]),
                mocker.call(_check_interval_passed, [150]),
            ]
            mock_apply.assert_has_calls(calls, any_order=True)
            assert mock_apply.call_count == 2
            calls = [mocker.call()]
            mock_async.return_value.get.assert_has_calls(calls, any_order=True)
            assert mock_async.return_value.get.call_count == 2
            calls = [mocker.call()]
            mock_async.return_value.wait.assert_has_calls(calls, any_order=True)
            assert mock_async.return_value.wait.call_count == 2
            mocked_logger.return_value.warning.assert_called_once()
            mocked_logger.return_value.warning.assert_called_once_with(
                "Cycle duration: 80"
            )

    def test_core_permission_providers_updater_run_permissions_update_logs_async_error(
        self, mocker
    ):
        pool, logger = self._setup_single_cycle(mocker)
        pool.apply_async.side_effect = Exception("boom")
        run_permissions_update()
        logger.exception.assert_called_once()

    def test_core_permission_providers_updater_run_permissions_update_logs_result_error(
        self, mocker
    ):
        pool, logger = self._setup_single_cycle(mocker)
        pool.apply_async.return_value.get.side_effect = Exception("boom")
        run_permissions_update()
        logger.exception.assert_called_once()

    def test_core_permission_providers_updater_run_permissions_update_logs_cycle_info(
        self, mocker
    ):
        pool, logger = self._setup_single_cycle(mocker)
        mocker.patch(f"{MODULE}.divmod", return_value=(0, 0), create=True)
        run_permissions_update()
        logger.info.assert_called_once()
        logger.exception.assert_not_called()
