"""Testing module for :py:mod:`utils.permissions` module."""

import signal
from unittest import mock

import utils.permissions
from utils.constants.core import PERMISSIONS_TTL, QUARTER
from utils.permissions import (
    _check_interval_passed,
    _exit_gracefully,
    _initializer,
    _process_permission_dapp,
    run_permissions_update,
)


class TestUtilsPermissionsProcessFunctions:
    """Testing class for :class:`utils.permissions` process functions."""

    # # _process_permission_dapp
    def test_utils_permissions_process_permission_dapp_functionality(self, mocker):
        mocked_check = mocker.patch(
            "utils.permissions.check_and_update_permission_dapp_boxes"
        )
        _process_permission_dapp()
        mocked_check.assert_called_once()
        mocked_check.assert_called_with()


class TestUtilsPermissionsHelperFunctions:
    """Testing class for :class:`utils.permissions` main functions."""

    # # _check_interval_passed
    def test_utils_transmitters_check_interval_passed_for_last_timestamp_none(
        self, mocker
    ):
        last_timestamp = None
        mocked_pause = mocker.patch("utils.permissions.pause")
        with mock.patch("utils.permissions.datetime") as mocked_datetime:
            returned = _check_interval_passed(last_timestamp)
        assert returned == mocked_datetime.now.return_value.timestamp.return_value
        mocked_pause.assert_not_called()

    def test_utils_transmitters_check_interval_passed_functionality(self, mocker):
        last_timestamp = 123456789
        mocked_pause = mocker.patch("utils.permissions.pause")
        with mock.patch("utils.permissions.datetime") as mocked_datetime:
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

    # # _exit_gracefully
    def test_utils_permissions_exit_gracefully_functionality(self):
        assert utils.permissions.exit_signal is False
        _exit_gracefully()
        assert utils.permissions.exit_signal is True

    # # _initializer
    def test_utils_permissions_initializer_functionality(self, mocker):
        mocked_logger = mocker.patch("utils.permissions.create_multiprocess_logger")
        with mock.patch("utils.permissions.os.getpid") as mocked_pid:
            _initializer()
            mocked_pid.assert_called_once()
            mocked_pid.assert_called_with()
        assert utils.permissions.logger == mocked_logger.return_value
        mocked_logger.assert_called_once()
        mocked_logger.assert_called_with(mocked_pid.return_value)


class TestUtilsPermissionsRunPermissionsUpdate:
    """Testing class for :py:func:`utils.permissions.run_permissions_update`."""

    def _setup_single_cycle(self, mocker):
        utils.permissions.exit_signal = False
        mocker.patch("utils.permissions.signal")
        mocked_time = mocker.patch("utils.permissions.time")
        mocked_time.time.side_effect = [0.0, 0.0]
        mocked_logger = mocker.patch("utils.permissions.create_multiprocess_logger")
        mocked_pool_class = mocker.patch("utils.permissions.Pool")
        pool = mocked_pool_class.return_value.__enter__.return_value

        def stop(*args, **kwargs):
            utils.permissions.exit_signal = True

        pool.apply.side_effect = stop
        return pool, mocked_logger.return_value

    # # run_permissions_update
    def test_utils_permissions_run_permissions_update_exits_loop_for_exit_signal_true(
        self, mocker
    ):
        with (
            mock.patch.object(utils.permissions, "exit_signal", True),
            mock.patch("utils.permissions.create_multiprocess_logger") as mocked_logger,
            mock.patch("utils.permissions.Pool") as mocked_pool,
            mock.patch("utils.permissions.signal.signal") as mocked_signal,
            mock.patch("utils.permissions.os.getpid") as mocked_pid,
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
            mocked_logger.assert_called_once()
            mocked_logger.assert_called_with(
                mocked_pid.return_value, prefix="permissions"
            )
            mocked_pool.assert_called_once()
            mocked_pool.assert_called_with(
                processes=1, initializer=utils.permissions._initializer
            )
            mock_close.assert_called_once()
            mock_close.assert_called_with()
            mock_join.assert_called_once()
            mock_join.assert_called_with()
            mock_apply.assert_not_called()

    def test_utils_permissions_run_permissions_update_doesnt_log(self, mocker):
        with (
            mock.patch.object(utils.permissions, "exit_signal", False),
            mock.patch("utils.permissions.create_multiprocess_logger") as mocked_logger,
            mock.patch("utils.permissions.Pool") as mocked_pool,
            mock.patch("utils.permissions.signal.signal"),
            mock.patch("utils.permissions.os.getpid"),
            mock.patch("utils.permissions.time.time", side_effect=[1, 10]),
        ):
            mock_apply, mock_async = mocker.MagicMock(), mocker.MagicMock()
            mocked_pool.return_value.__enter__.return_value.apply = mock_apply
            mocked_pool.return_value.__enter__.return_value.apply_async = mock_async
            mock_async.return_value.wait.side_effect = _exit_gracefully
            run_permissions_update()
            mock_apply.assert_called_once()
            mock_apply.assert_called_with(
                utils.permissions._check_interval_passed, [None]
            )
            mock_async.return_value.get.assert_called_once()
            mock_async.return_value.get.assert_called_with()
            mock_async.return_value.wait.assert_called_once()
            mock_async.return_value.wait.assert_called_with()
            mocked_logger.return_value.warning.assert_not_called()

    def test_utils_permissions_run_permissions_update_logs_timeout(self, mocker):
        with (
            mock.patch.object(utils.permissions, "exit_signal", False),
            mock.patch("utils.permissions.create_multiprocess_logger") as mocked_logger,
            mock.patch("utils.permissions.Pool") as mocked_pool,
            mock.patch("utils.permissions.signal.signal"),
            mock.patch("utils.permissions.os.getpid"),
            mock.patch("utils.permissions.time.time", side_effect=[100, 110, 120, 200]),
        ):
            mock_apply, mock_async = mocker.MagicMock(), mocker.MagicMock()
            mocked_pool.return_value.__enter__.return_value.apply = mock_apply
            mocked_pool.return_value.__enter__.return_value.apply_async = mock_async
            mocked_logger.return_value.warning.side_effect = _exit_gracefully
            mock_apply.return_value = 150
            run_permissions_update()
            calls = [
                mocker.call(utils.permissions._check_interval_passed, [None]),
                mocker.call(utils.permissions._check_interval_passed, [150]),
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
            mocked_logger.return_value.warning.assert_called_with("Cycle duration: 80")

    def test_utils_permissions_run_permissions_update_logs_apply_async_error(
        self, mocker
    ):
        pool, logger = self._setup_single_cycle(mocker)
        pool.apply_async.side_effect = Exception("boom")
        run_permissions_update()
        logger.exception.assert_called_once()

    def test_utils_permissions_run_permissions_update_logs_result_error(self, mocker):
        pool, logger = self._setup_single_cycle(mocker)
        pool.apply_async.return_value.get.side_effect = Exception("boom")
        run_permissions_update()
        logger.exception.assert_called_once()

    def test_utils_permissions_run_permissions_update_logs_cycle_info(self, mocker):
        pool, logger = self._setup_single_cycle(mocker)
        mocker.patch("utils.permissions.divmod", return_value=(0, 0), create=True)
        run_permissions_update()
        logger.info.assert_called_once()
        logger.exception.assert_not_called()
