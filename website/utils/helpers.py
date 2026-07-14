"""Module containing helper functions.

`Asset` and `asset` represent either Algod client's or Tinyman's asset data.
`Asa` and `asa` represent Asa named tuple.
`amount` reporesents amount/quantity in ASA.
`value` reporesents amount in Algo.
"""

import base64
import calendar
import hashlib
import json
import logging
import multiprocessing
import os
import random
import re
import time

from algosdk.encoding import is_valid_address
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.http import url_has_allowed_host_and_scheme

from nameservice.main import check_name
from utils.cache import cached_bundle, cupdate_bundle
from utils.clients import algod_instance, redis_instance
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


def parse_export_limits(raw):
    """Translate "free:5,Intro:6,Asastatser:7,..." into an int-valued dict.

    Blank or malformed entries are skipped; missing tiers fall back to the
    module defaults in exportpermissions._DEFAULT_LIMITS at read time.

    :param raw: comma-separated tier configurations
    :type raw: str
    :var limits: evaluated collection of tier limits mapped to sizes
    :type limits: dict
    :var part: current segment of the raw string being parsed
    :type part: str
    :var key: parsed tier name
    :type key: str
    :var sep: parsed separator character
    :type sep: str
    :var value: parsed limit size for the tier
    :type value: str
    :return: dict
    """
    limits = {}
    for part in raw.split(","):
        key, sep, value = part.partition(":")
        key = key.strip()
        if not key or not sep:
            continue

        try:
            limits[key] = int(value.strip())

        except ValueError:
            continue

    return limits


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


def check_bundle_addresses(bundle):
    """Return addresses from cache client associated with provided bundle.

    :param bundle: hash value associated with target addresses
    :type bundle: str
    :var cache_client: Redis client instance
    :type cache_client: :class:`Redis`
    :return: str
    """
    cached = cached_bundle(bundle, redis_instance())
    return cached if cached is not False else ""


def create_bundle(addresses):
    """Return bundle hash from `addresses` and update cache if needed.

    :param addresses: Algorand addresses separated by spaces
    :type addresses: string
    :var bundle: hash made from provided addresses
    :type bundle: str
    :var cache_client: Redis client instance
    :type cache_client: :class:`Redis`
    :return: str
    """
    bundle = bundle_from_addresses(addresses)
    cache_client = redis_instance()
    if not cached_bundle(bundle, cache_client):
        cupdate_bundle(bundle, addresses, cache_client)

    return bundle


def load_transparency_reports():
    """Scan the static assets directory for ASA Stats transparency reports.

    :var reports_dir: absolute path to the static assets directory
    :type reports_dir: str
    :var pattern: compiled regex pattern to match transparency report filenames
    :type pattern: re.Pattern
    :return: list
    """
    reports_dir = os.path.join(settings.STATIC_ROOT, "assets")
    pattern = re.compile(r"^asastats-transparency-report-(\d{4})-(\d{2})\.pdf$")

    reports_by_year = {}

    # Safely scan the directory
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            match = pattern.match(filename)
            if match:
                year_int = int(match.group(1))
                month_int = int(match.group(2))

                if year_int not in reports_by_year:
                    reports_by_year[year_int] = []

                reports_by_year[year_int].append(
                    {
                        "year": match.group(1),
                        "month": match.group(2),
                        "short_year": match.group(1)[-2:],
                        "month_name": calendar.month_name[month_int],
                    }
                )

    # Sort years descending, and months descending within each year
    sorted_reports = []
    for year in sorted(reports_by_year.keys(), reverse=True):
        sorted_months = sorted(
            reports_by_year[year], key=lambda x: x["month"], reverse=True
        )
        sorted_reports.append({"year": year, "months": sorted_months})

    return sorted_reports


def random_slogan():
    """Return random slogan text from predefined collection.

    :return: str
    """
    return random.choice(ASASTATS_SLOGANS)


def safe_referer(request):
    """Return a same-origin ``Referer`` for ``request``, or ``None``.

    Used to bounce the user back to the address page they clicked Swap from
    (validated, never trusted, to avoid an open redirect).

    :param request: the current request
    :type request: rest_framework.request.Request | django.http.HttpRequest
    :return: a safe local URL, or None
    :rtype: str | None
    """
    referer = request.META.get("HTTP_REFERER", "")
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return referer

    return None


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
