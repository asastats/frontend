"""Module containing helper functions.

`Asset` and `asset` represent either Algod client's or Tinyman's asset data.
`Asa` and `asa` represent Asa named tuple.
`amount` reporesents amount/quantity in ASA.
`value` reporesents amount in Algo.
"""

import base64
import hashlib
import json
import logging
import multiprocessing
import os
import random
import time

from algosdk.encoding import is_valid_address
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError

from nameservice.main import check_name
from utils.clients import algod_instance
from utils.constants.core import (
    ASASTATS_SLOGANS,
    BANNERS,
    DEFAULT_SLEEP_INTERVAL,
    INVALID_ADDRESS_TEXT,
    MISSING_ENVIRONMENT_VARIABLE_ERROR,
)

logger = logging.getLogger(__name__)


# # HELPER FUNCTIONS
def base64_to_utf(base64_message):
    """Return provided base64 value converted to UTF string.

    :param base64_message: base64 encoded value
    :type base64_message: str
    :param base64_bytes: base64 message as bytes binary
    :type base64_bytes: bytes
    :return: str
    """
    if not base64_message:
        return ""
    try:
        base64_bytes = base64_message.encode("utf8")
        return base64.b64decode(base64_bytes).decode("utf8")
    except UnicodeDecodeError:
        return ""


def check_algorand_address(entry, raise_error=False):
    """Check for `entry` validity and return provided entry/address

    or nameservice addresses if it's a name.

    Return empty string if it's not a valid Algorand address.
    Raise ValidationError for an invalid address if provided `raise_error` is True.

    :param address: Algorand address or nameservice name
    :type address: str
    :param raise_error: whether ValidationError should be raised for invalid address
    :type raise_error: Boolean
    :var addresses: evaluated collection of Algorand addresses separated by spaces
    :type addresses: str
    :var _address: current Algorand address to check for validity
    :type _address: str
    :var valid_address: value indicating if address is a valid entry
    :type valid_address: Boolean
    :return: str
    """
    addresses = check_name(entry, algod_instance())
    for _address in addresses.split(" "):
        valid_address = is_valid_address(_address)
        if not valid_address and raise_error:
            raise ValidationError(INVALID_ADDRESS_TEXT)
        elif not valid_address:
            return ""
    return addresses


def create_multiprocess_logger(identifier, prefix="process", level=logging.INFO):
    """Create and return logger instance used in multiprocessing environemnt.

    :param identifier: unique process identifier
    :type identifier: str
    :param prefix: prefix to use for defining logging filename
    :type prefix: str
    :var logger: logger instance
    :type logger: :class:`logging.Logger`
    :var name: current process name
    :type name: str
    :var file_handler: instance that writes formatted logging records to disk files
    :type file_handler: :class:`logging.FileHandler`
    :var formatter: instance that converts a LogRecord to text
    :type formatter: :class:`logging.Formatter`
    :return: :class:`logging.Logger`
    """
    logger = multiprocessing.get_logger()
    name = multiprocessing.current_process().name
    logger.setLevel(level)
    file_handler = logging.FileHandler(
        settings.DATA_PATH / "logs" / f"{prefix}_{name}_{identifier}.log"
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    return logger


def get_env_variable(name, default=None):
    """Return environment variable with provided `name`.

    Raise `ImproperlyConfigured` exception if such variable isn't set.

    :param name: name of environment variable
    :type name: str
    :return: str
    """
    try:
        return os.environ[name]
    except KeyError:
        if default is None:
            raise ImproperlyConfigured(
                "{} {}!".format(name, MISSING_ENVIRONMENT_VARIABLE_ERROR)
            )
        return default


def message_for_app_code_in_values(values, app_codes, msg):
    """Return provided message if any code from provided is found in provided values.

    :param values: collection of account's assets swap values
    :type values: :class:`utils.structs.Values`
    :param app_codes: collection of provider base app prefixes
    :type app_codes: list
    :param msg: message to return if app is in values
    :type msg: str
    :return: str
    """
    if any(
        any(val[0].startswith(item) for item in app_codes)
        for row in values
        for val in row[3]
        if len(row[3])
    ):
        return msg
    return ""


def pause(seconds=DEFAULT_SLEEP_INTERVAL):
    """Sleep for provided number of seconds.

    :param seconds: number of seconds to pause
    :type seconds: int
    """
    time.sleep(seconds)


def read_json(filename):
    """Return content of JSON file located in provided `filename`.

    :param filename: full path to JSON file to read
    :type filename: str
    :return: dict
    """
    if os.path.exists(filename):
        with open(filename, "r") as json_file:
            try:
                return json.load(json_file)

            except json.JSONDecodeError:
                pass

    return {}


# # PUBLIC FUNCTIONS
def bundle_from_addresses(addresses):
    """Canonical bundle hash. DO NOT MODIFY.

    Forks and the backend must produce byte-identical hashes, so input is
    normalized here: ``split()`` collapses any whitespace run and drops empty
    tokens, ``set`` de-duplicates, ``sorted`` makes order deterministic. SHA-1
    over UTF-8 of ASCII base32 addresses is identical on every platform.

    :param addresses: Algorand addresses separated by whitespace
    :return: 40-char uppercase hex digest
    """
    tokens = sorted({a for a in addresses.split() if a})
    return hashlib.sha1(" ".join(tokens).encode("utf-8")).hexdigest().upper()


def check_bundle_addresses(bundle, cache_client=False):
    """Resolve a bundle hash to its space-separated addresses.

    The open app owns this mapping (BundleName), not the engine cache.

    :param bundle: 40-hex bundle hash
    :return: space-separated addresses, or "" if the hash is unknown locally
    """
    if not bundle:
        return ""
    from core.models import BundleName  # local import avoids an app-loading cycle

    return (
        BundleName.objects.filter(bundle=bundle)
        .values_list("addresses", flat=True)
        .first()
        or ""
    )


def create_bundle(addresses, cache_client=False):
    """Return the bundle hash for ``addresses`` (no local cache write needed)."""
    return bundle_from_addresses(addresses)


def random_slogan():
    """Return random slogan text from predefined collection.

    :return: str
    """
    return random.choice(ASASTATS_SLOGANS)


def weighted_randomized_banner(banners=BANNERS):
    """Select a single banner from a list based on their assigned weights.

    :param banners: collection of banners data
    :type banners: list
    :var weights: collection of existing banner weights
    :type weights: list
    :return: dict
    """
    if not banners:
        return {}

    # Create a list of just the weights: [4, 2, 1]
    weights = [banner.get("weight", 1) for banner in banners]

    # random.choices returns a list of k elements, so we grab the first one [0]
    return random.choices(banners, weights=weights, k=1)[0]
