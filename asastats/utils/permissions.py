"""Module containing Permission dApp update functions and classes."""

import os
import signal
import time
from datetime import UTC, datetime
from multiprocessing import Pool

from permissiondapp.dapp.foundation import (
    check_and_update_permission_dapp_boxes,
)
from utils.constants.core import PERMISSIONS_TTL, QUARTER
from utils.helpers import create_multiprocess_logger, pause

exit_signal = False


# # PROCESS
def _process_permission_dapp():
    """Call updating poermission dApp boxes routine."""
    check_and_update_permission_dapp_boxes()


# # MAIN
def _check_interval_passed(last_timestamp):
    """Return new round from Node after it is available.

    :param last_timestamp: timestamp when last cycle started
    :type last_timestamp: float
    :var current_round: current Node round
    :type current_round: int
    :return: int
    """
    while True:
        current_timestamp = datetime.now(UTC).timestamp()
        if (
            last_timestamp is None
            or current_timestamp > last_timestamp + PERMISSIONS_TTL
        ):
            break
        pause(QUARTER)

    return current_timestamp


def _exit_gracefully(*args):
    """Set exit signal variable to True."""
    global exit_signal
    exit_signal = True


def _initializer():
    """Initialize global variables needed for multiprocessing pool functioning."""
    global logger
    logger = create_multiprocess_logger(os.getpid())


def run_permissions_update():
    """Run infinite loop and update Permission dApp boxes."""
    signal.signal(signal.SIGINT, _exit_gracefully)
    signal.signal(signal.SIGTERM, _exit_gracefully)

    main_logger = create_multiprocess_logger(os.getpid(), prefix="permissions")
    last_timestamp = None
    counter = 0

    with Pool(processes=1, initializer=_initializer) as pool:
        while not exit_signal:
            start_time = time.time()

            last_timestamp = pool.apply(_check_interval_passed, [last_timestamp])

            async_results = []

            try:
                async_results.append(pool.apply_async(_process_permission_dapp))
            except Exception as e:
                main_logger.exception(e)

            for async_result in async_results:
                try:
                    async_result.get()
                except Exception as e:
                    main_logger.exception(e)

                async_result.wait()

            counter += 1
            duration = time.time() - start_time
            if duration > QUARTER * 80:
                main_logger.warning(f"Cycle duration: {duration}")

            else:
                if divmod(counter, 100)[1] == 0:
                    main_logger.info(f"Cycle duration: {duration}; {counter}")

        pool.close()
        pool.join()

    print("Gracefully exited.")
