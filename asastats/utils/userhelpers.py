"""Module containing helper functions for authenticated users."""

import logging
import re
import unicodedata

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from hashids import Hashids

from utils.clients import indexer_instance, search_transactions
from utils.constants.users import (
    ADDRESS_AND_ALGO_NAME_URL_PATH_ERROR,
    ADMPOOL_ADDRESS,
    ADMPOOL_AUTHORIZATION_MIN_ROUND,
    HASHIDS_SALT,
    MANDATORY_VALUES_SIZE,
)
from utils.helpers import base64_to_utf, check_algorand_address

logger = logging.getLogger(__name__)


# # VALUES
def _docs_positions_offset_and_length_pairs(
    docs_data_size, start=MANDATORY_VALUES_SIZE
):
    """Return offset/position and size pairs for docs values with size `docs_data_size`

    :param docs_data_size: size of serialized docs values
    :type docs_data_size: int
    :param start: starting position of documents' values
    :type start: int
    :return: list
    """
    return [
        (
            (start + (index // 2) * 9, 8)
            if divmod(index, 2)[1] == 0
            else (start + (index // 2) * 9 + 8, 1)
        )
        for counter, index in enumerate(range(30))
        if counter // 2 < docs_data_size // 9
    ]


def _extract_uint(byte_str, index, length):
    """Return extarcted uint from providedc byte string.

    :param byte_str: base64 encoded values
    :type byte_str: bytes
    :param index: target value's position/index in data
    :type index: int
    :param length: target value's bytes size/length
    :type length: int
    :return: int
    """
    return int.from_bytes(byte_str[index : index + length], byteorder="big")


def _starting_positions_offset_and_length_pairs(end=MANDATORY_VALUES_SIZE):
    """Return offset/position and related bytes size/length for starting values.

    Starting three pairs are:
    CALCULATED_DATA = ["votes", "permission"]
    SUBSCRIPTION_DATA = ["amount", "permission"]
    CURRENT_STAKING_DATA = ["amount", "permission"]

    :param end: starting values right boundary
    :type end: int
    :return: list
    """
    return [(offset, 8) for offset in range(0, end, 8)]


def _values_offset_and_length_pairs(docs_data_size):
    """Return offset/position and related bytes size/length of serialized values data.

    Provided `docs_data_size` represents size after mandatory starting size.

    :param docs_data_size: size of docs values pairs
    :type docs_data_size: int
    :return: list
    """
    return (
        _starting_positions_offset_and_length_pairs()
        + _docs_positions_offset_and_length_pairs(docs_data_size)
    )


# # HELPERS
def check_authorization_transaction(profile):
    """Fetch and return provided `profile` address' authorization transaction ID.

    :param profile: user profile instance
    :type profile: class:`core.models.Profile`
    :var indexer_client: Algorand Indexer client instance
    :type indexer_client: :class:`IndexerClient`
    :var note: profile's unique hash representing required note
    :type note: str
    :var params: arguments to search transactions Indexer method
    :type params: dict
    :var results: current set of results
    :type results: dict
    :var transaction: currently processed transaction
    :type transaction: dict
    :return: str
    """
    indexer_client = indexer_instance()
    note = profile.address_authorization_note().lower()
    params = {
        "txn_type": "pay",
        "min_round": ADMPOOL_AUTHORIZATION_MIN_ROUND,
        "address": ADMPOOL_ADDRESS,
        "address_role": "receiver",
    }
    results = search_transactions(params, indexer_client, delay=0.05)
    while results.get("transactions"):
        for transaction in results.get("transactions"):
            if transaction.get("sender") == profile.address and base64_to_utf(
                transaction.get("note", "")
            ) in (note, note.upper()):
                return transaction.get("id")

        results = search_transactions(
            params, indexer_client, next_page=results.get("next-token"), delay=0.05
        )

    return ""


def decode_unique_hash(uid, salt=HASHIDS_SALT):
    """Decode number from unique alphanumeric value.

    :param uid: unique hash
    :type uid: str
    :return: int
    """
    result = Hashids(salt=salt, min_length=3).decode(uid)
    return result[0] if result else 0


def delete_deactivated():
    """Delete all deactivated user accounts together with respective profile.

    :var count: current number of deleted users
    :type count: integer
    :var users: inactive user instances
    :type users: :class:`QuerySet`
    :return: int
    """
    count = 0
    users = get_user_model().objects.filter(is_active=False)
    for user in users:
        user.profile.delete()
        user.delete()
        count += 1

    return count


def is_system_reserved_url_path(url_path):
    """Return True if provided `url_path` is reserved by the system.

    :param url_path: URL path to check against the system
    :type url_path: str
    :return: Boolean
    """
    import asastats.urls
    import core.urls

    excluded = []
    for pattern in [
        str(url.pattern).rstrip("$").rstrip("/").lstrip("^")
        for url in asastats.urls.urlpatterns + core.urls.urlpatterns
    ]:
        segment = pattern.split("/")[0]
        if ">(" in segment:
            excluded.extend(
                segment[segment.index(">(") + 2 : segment.index(")")].split("|")
            )
        elif segment:
            excluded.append(segment)
    return url_path in excluded


def slugified_bundle_name(value, allow_unicode=False):
    """Return a slug of `value` allowing the dot character, Django-style.

    NOTE: this is rewrite of Django's `slugify` with added dot (.) as allowed character

    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.

    :param value: bundle name to slugify
    :type value: str
    :param allow_unicode: keep unicode characters instead of ASCII-folding
    :type allow_unicode: bool
    :return: str
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\.\w\s-]", "", value)
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def truncated_timestamp_and_address(timestamp, address):
    """Return integer created from provided timestamp.

    :param timestamp: seconds since epoch
    :type timestamp: float
    :param address: public Algorand address
    :type address: str
    :var address_repr: representation of public Algorand address converted to int
    :type address_repr: str
    :return: int
    """
    address_repr = str(int(address.encode().hex(), 16))
    return (
        int(str(timestamp).replace(".", "")[-5:])
        + int(address_repr[:5])
        + int(address_repr[-5:])
    )


def unique_hash_from_number(number, salt=HASHIDS_SALT):
    """Get unique alphanumeric value based on supplied number.

    :param number: number to convert into hashids unique id
    :type number: int
    :return: str
    """
    hashids = Hashids(salt=salt, min_length=3)
    return hashids.encode(number)


def user_display(user):
    """Return human readable representation of provided `user` instance.

    :param user: user instance
    :type user: class:`django.contrib.auth.models.User`
    :return: str
    """
    return user.profile.name


def validate_address_or_algo_name_url_path(url_path):
    """Raise ValidationError if provided `url_path` is Algorand address or .algo name.

    :param url_path: URL path to check
    :type url_path: str
    """
    response = check_algorand_address(url_path)
    if response:
        raise ValidationError(ADDRESS_AND_ALGO_NAME_URL_PATH_ERROR)
