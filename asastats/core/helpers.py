"""Module containing core app helper functions."""

import re

from algosdk.constants import ADDRESS_LEN
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404

from api.client import export_status
from api.client import reset_export as _reset_export
from api.client import start_export as _start_export
from core.models import BundleName
from core.templatetags.core_extras import short_address
from utils.charts import prepare_consolidated_charts
from utils.constants.core import (
    BUNDLE_SEPARATION_CHARS,
    FORBIDDEN_ADDRESSES,
    INVALID_ADDRESS_TEXT,
    MAX_BUNDLE_SIZE,
)
from utils.constants.tax import TAX_DURATION_MESSAGE
from utils.constants.users import (
    BUNDLE_ADDRESSES_LIMIT_HELP_TEXT,
    PUBLIC_BUNDLE_ADDRESSES_LIMIT_HELP_TEXT,
    PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT,
)
from utils.helpers import (
    check_algorand_address,
    check_bundle_addresses,
    message_for_app_code_in_values,
)


## RAW PARSING
def _normalize_collection(collection, max_bundle_size=MAX_BUNDLE_SIZE):
    """Return collection of Algorand addresses from provided collection.

    An item in collection can either be an Algorand address, empty string
    or string of addresses separated by spaces.

    :param collection:  address or addresses separated by spaces collection
    :type collection: generator
    :param max_bundle_size: maximum allowed addresses count in bundle
    :type max_bundle_size: int
    :return: list
    """
    bundle = []
    for entry in collection:
        if " " in entry:
            bundle.extend(entry.split(" "))
        elif entry:
            bundle.append(entry)
    return bundle[:max_bundle_size]


def _parse_bundle(data):
    """Return collection of parsed addresses and/or nameservices' entries.

    :param data: multiple entries data from bundle field
    :type data: str
    :return: generator
    """
    return (
        check_algorand_address(_strip_address(address))
        for address in re.split("|".join(BUNDLE_SEPARATION_CHARS) + "|\n", data)
    )


def _strip_address(address):
    """Strip and return address without any separation characters.

    :param address: address including bundle separation character
    :type address: str
    :return: str
    """
    return address.strip().strip("".join(BUNDLE_SEPARATION_CHARS))


def addresses_from_raw(raw, address_data="", max_bundle_size=MAX_BUNDLE_SIZE):
    """Return address or multiple addresses separated by spaces.

    Raise ValidationError if raw content isn't a valid Algorand address.

    :var raw: multiple entries data from bundle field
    :type raw: str
    :var address_data: data from address field
    :type address_data: str
    :param max_bundle_size: maximum allowed addresses count in bundle
    :type max_bundle_size: int
    :var bundle: parsed collection of addresses
    :type bundle: list
    :return: str
    """
    if not raw:
        if not address_data:
            raise ValidationError(INVALID_ADDRESS_TEXT)

        if len(address_data) == ADDRESS_LEN:
            return check_algorand_address(address_data, raise_error=True)
        raw = address_data

    bundle = _normalize_collection(_parse_bundle(raw), max_bundle_size=max_bundle_size)
    if bundle:
        return " ".join(address for address in set(bundle) if address)

    raise ValidationError(INVALID_ADDRESS_TEXT)


def check_forbidden_addresses(value):
    """Raiose 404 error if value contains any forbidden address.

    :param value: space delimited addresses
    :type value: str
    """
    if any(address in value for address in FORBIDDEN_ADDRESSES):
        raise Http404


def context_with_consolidated_data(context, serialized_data):
    """Update provided `context` with consolidated data created from `serialized_data`.

    :param context: object containing all the data needed for rendering
    :type context: dict
    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :var context["distchart"]: data for rendering top ASA distribution chart
    :type context["distchart"]: dict
    :var context["ratiochart"]: data for rendering ALGO/ASA/NFT chart
    :type context["ratiochart"]: dict
    :var context["nftfloorchart"]: data for rendering NFT floors chart
    :type context["nftfloorchart"]: dict
    :var context["consolidated"]: consolidated view totals
    :type context["consolidated"]: :class:`utils.structs.Consolidated`
    :return: dict
    """
    (
        context["distchart"],
        context["ratiochart"],
        context["nftfloorchart"],
        context["consolidated"],
    ) = prepare_consolidated_charts(
        serialized_data,
        context["asas"],
        context["values"],
        context["total"],
        context["nft_colors"],
    )
    return context


# # TAX CLIENT-SIDE
def _send_duration_messages(request):
    """Create and emit Django messages about varying CSV files creation duration.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :var paragraph: currenty processed paragraph of text
    :type paragraph: str
    """
    for paragraph in TAX_DURATION_MESSAGE.split("\n"):
        messages.success(request, "-" * 5)
        messages.success(request, paragraph)


def _send_enqueued_messages(request, addresses):
    """Create and emit Django message for each address in `addresses` collection.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param addresses: public Algorand addresses separated by spaces
    :type addresses: str
    :var address: currently processed public Algorand address
    :type address: str
    :var shorten: current address' shortened representation
    :type shorten: str
    """
    for address in addresses.split(" "):
        shorten = short_address(address)
        messages.success(request, f"{shorten} enqueued for processing!")


def check_export_status(url_value):
    """Return tax data from cache for provided `url_value`.

    :param url_value: address or bundle value found in url
    :type url_value: str
    :return: dict
    """
    return export_status(url_value)


def prepare_tax_context(context, url_value):
    """Prepare tax context object for provided `url_value`.

    :param context: object containing all the data needed for rendering
    :type context: dict
    :param url_value: address or bundle value found in url
    :type url_value: str
    :var typ: type of entry (address or bundle)
    :type typ: str
    :var addresses: address(es) value found in url
    :type addresses: str
    :return: dict
    """
    typ, addresses = (
        ("address", url_value)
        if len(url_value) > 50
        else ("bundle", check_bundle_addresses(url_value))
    )
    context[typ] = addresses.split(" ")
    context["url_value"] = url_value
    return context


def reset_export(url_value):
    """Reset cache data for provided `url_value` and call zip deletion consumer task.

    :param url_value: address or bundle value found in url
    :type url_value: str
    """
    return _reset_export(url_value)


def start_export(url_value, addresses, request, **kwargs):
    """Start addresss processing task and record it.

    :param url_value: address or bundle value found in url
    :type url_value: str
    :param addresses: public Algorand addresses separated by spaces
    :type addresses: str
    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    """
    _send_enqueued_messages(request, addresses)  # keep the open UX messaging
    return _start_export(url_value, addresses)  # backend enqueues process_addresses


# # PUBLIC BUNDLES
def _check_public_bundles_eligibility():
    """Return collection of all eligible public bundle instances.

    :var bundlenames: profile's bundle names collection
    :type bundlenames: :class:`QuerySet`
    :return: list
    """
    bundlenames = BundleName.objects.filter(public=True)
    return [
        bundlename
        for bundlename in bundlenames
        if bundlename.is_eligible_public_bundlename()
    ]


def _create_public_bundle_files(hashes):
    """Create files from provided collection of hashes/filenames.

    :param hashes: collection of bundle names and related bundle hashes
    :type hashes: list
    :var bundlenames_path: full path to public bundles directory
    :type bundlenames_path: :class:`pathlib.PosixPath`
    :var bundle_hash: currently processed bundle hash
    :type bundle_hash: str
    """
    bundlenames_path = settings.DATA_PATH / "bundles"
    for bundle_hash in hashes:
        (bundlenames_path / bundle_hash).touch()


def _delete_public_bundle_files(hashes):
    """Delete all files from provided collection of hashes/filenames.

    :param hashes: collection of bundle names and related bundle hashes
    :type hashes: list
    :var bundlenames_path: full path to public bundles directory
    :type bundlenames_path: :class:`pathlib.PosixPath`
    :var bundle_hash: currently processed bundle hash
    :type bundle_hash: str
    """
    bundlenames_path = settings.DATA_PATH / "bundles"
    for bundle_hash in hashes:
        (bundlenames_path / bundle_hash).unlink()


def _public_bundle_filenames():
    """Return collection of all existing filenames/hashes found on disk.

    :var bundlenames_path: full path to public bundles directory
    :type bundlenames_path: :class:`pathlib.PosixPath`
    :return: set
    """
    bundlenames_path = settings.DATA_PATH / "bundles"
    return {
        filename.stem for filename in bundlenames_path.glob("*") if "_" in filename.stem
    }


def _public_bundles_collection():
    """Return collection of all public bundle hashes and instances.

    :return: list
    """
    return [
        (f"{bundlename.name.lower()}_{bundlename.bundle}", bundlename)
        for bundlename in _check_public_bundles_eligibility()
    ]


def check_public_bundles():
    """Check and add new and delete obsolete public bundle name filenames.

    Return collection of updated bundle names.

    :param bundlenames: collection of all instances of public bundle names
    :type bundlenames: list
    :var hashes: collection of all public bundle name hashes
    :type hashes: set
    :var filenames: collection of all existing filenames/hashes found on disk
    :type filenames: set
    :var missing: collection of public bundle name hashes not found on disk
    :type missing: set
    :var obsolete: collection of filenames that aren't valid public bundle names
    :type obsolete: set
    :return: list
    """
    bundlenames = _public_bundles_collection()
    hashes = {bundlename[0] for bundlename in bundlenames}
    filenames = _public_bundle_filenames()
    missing = hashes - filenames
    obsolete = filenames - hashes
    if missing:
        _create_public_bundle_files(missing)

    if obsolete:
        _delete_public_bundle_files(obsolete)

    return [
        "_".join(bundle_hash.split("_")[:-1]) for bundle_hash in missing.union(obsolete)
    ]


def format_addresses_limit_help_text(bundlename):
    """Return formatted help text for provided bundle instance.

    :param bundlename: bundle name instance
    :type bundlename: :class:`core.models.BundleName`
    :var help_text: addresses field's help text
    :type help_text: str
    :var limit_public: number of addresses allowed in a public bundle
    :type limit_public: int
    :var public_help_text: addresses field's help text related to public bundle
    :type public_help_text: str
    """
    help_text = BUNDLE_ADDRESSES_LIMIT_HELP_TEXT.format(
        bundlename.profile.bundle_size_limit(bundlename)
    )
    limit_public = bundlename.profile.bundle_size_limit_for_public()
    public_help_text = (
        PUBLIC_BUNDLE_ADDRESSES_LIMIT_HELP_TEXT.format(limit_public)
        if limit_public
        else PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT
    )
    return help_text + public_help_text
