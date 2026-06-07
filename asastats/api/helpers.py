"""Module containing api app post-processing helpers."""

from algosdk.constants import ADDRESS_LEN
from algosdk.encoding import is_valid_address
from django.utils.text import slugify
from rest_framework.serializers import ValidationError

import api.serializers
from core.helpers import _normalize_collection, _parse_bundle
from utils.constants.apiv2 import (
    INVALID_ADDRESS_INPUT_TEXT,
    INVALID_INPUT_TEXT,
    INVALID_NFD_NAME_TEXT,
    INVALID_RAW_TEXT,
)
from utils.constants.core import INVALID_ADDRESS_TEXT, INVALID_BUNDLE_TEXT
from utils.helpers import (
    check_algorand_address,
    check_bundle_addresses,
    create_bundle,
)


def _convert_algo_value_to_usd(value, pricealgo):
    """Return a single ALGO value converted to a formatted USD string.

    :param value: value in ALGO
    :type value: str
    :param pricealgo: ALGO price in USDC
    :type pricealgo: str
    :return: str
    """
    return "{0:.6f}".format(float(value) * float(pricealgo))


def convert_asaitems_values_to_usd(asaitems, pricealgo):
    """Return ASA items collection with all the values converted to USD.

    :param asaitems: serialized evaluated account's ASA items collection
    :type asaitems: list
    :param pricealgo: ALGO price in USDC
    :type pricealgo: str
    :return: list
    """
    return [
        {
            **item,
            "value": _convert_algo_value_to_usd(item.get("value", 0), pricealgo),
            **{
                "programs": _convert_programs_values_to_usd(
                    item.get("programs", []), pricealgo
                )
            },
        }
        for item in asaitems
    ]


def convert_items_values_to_usd(items, pricealgo, process_keys=["value"]):
    """Return collection of dictionaries with all the "values" keys converted to USD.

    :param items: collection of dictionaries having value key
    :type items: list
    :param pricealgo: ALGO price in USDC
    :type pricealgo: str
    :return: list
    """
    return [
        {
            **item,
            **{
                key: _convert_algo_value_to_usd(item.get(key, 0), pricealgo)
                for key in process_keys
            },
        }
        for item in items
    ]


def convert_nftcollections_values_to_usd(nftcollections, pricealgo):
    """Return serialized account's NFT collections with all the values converted to USD.

    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: list
    :param pricealgo: ALGO price in USDC
    :type pricealgo: str
    :return: list
    """
    return (
        {
            **item,
            "value": _convert_algo_value_to_usd(item.get("value", 0), pricealgo),
            **{
                "nfts": convert_items_values_to_usd(
                    item.get("nfts", []), pricealgo, process_keys=["value", "price"]
                )
            },
        }
        for item in nftcollections
    )


def _convert_programs_values_to_usd(programs, pricealgo):
    """Return serialized account's NFT items with all the values converted to USD.

    :param programs: serialized evaluated account's ASA item program instances
    :type programs: list
    :param pricealgo: ALGO price in USDC
    :type pricealgo: str
    :return: list
    """
    return [
        {
            **program,
            "value": _convert_algo_value_to_usd(program.get("value", 0), pricealgo),
            **(
                {
                    "linked": convert_items_values_to_usd(
                        program.get("linked"), pricealgo
                    )
                }
                if program.get("linked")
                else {}
            ),
        }
        for program in programs
    ]


def convert_account_values_to_usd(serialized_data, pricealgo):
    """Return serialized account's data with all the values converted to USD.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param pricealgo: ALGO price in USDC
    :type pricealgo: str
    :return: dict
    """
    return {
        **serialized_data,
        "account_info": {**serialized_data.get("account_info"), "values_in": "USD"},
        "asaitems": convert_asaitems_values_to_usd(
            serialized_data.get("asaitems"), pricealgo
        ),
        "nftcollections": convert_nftcollections_values_to_usd(
            serialized_data.get("nftcollections"), pricealgo
        ),
    }


def _check_provider_name(provider, name):
    """Return True if `provider` represents program's `name`.

    :param provider: unique dApp provider slug
    :type provider: str
    :param name: unique dApp provider name
    :type name: str
    :return: list generator
    """
    return (
        provider.lower() == slugify(name)
        or provider.lower() == name.split(" ")[0].lower()
    )


def _check_program_name(program_slug, name):
    """Return True if `program_slug` represents program's `name`.

    TODO: refactor

    :param program_slug: dApp program slug
    :type program_slug: str
    :param name: dApp provider program name
    :type name: str
    :var filtered_program: filtered dApp program slug
    :type filtered_program: str
    :var filtered_name: slugified and filtered dApp provider program name
    :type filtered_name: str
    :return: list generator
    """
    filtered_program = program_slug
    filtered_name = name

    if filtered_program.split("-")[-1].isnumeric():
        filtered_program = "-".join(filtered_program.split("-")[:-1])

    if "#" in filtered_name:
        filtered_name = filtered_name.split("#")[0].rstrip()

    filtered_program = (
        slugify(filtered_program)
        .replace("staking", "stake")
        .replace("farming", "farm")
        .replace("staking-reward", "reward")
        .replace("limit", "orders")
    )
    filtered_name = (
        slugify(filtered_name)
        .replace("staking", "stake")
        .replace("farming", "farm")
        .replace("staking-reward", "reward")
        .replace("added-liquidity", "liquidity")
    )

    return (
        True
        if ("orders" in filtered_program and "orders" in filtered_name)
        else filtered_program == filtered_name
    )


def _check_program_type(type_slug, check_name, check_typ):
    """Return True if `program_type` represents program's `name`.

    :param type_slug: program name user enetered
    :type type_slug: str
    :param check_name: dApp program name
    :type check_name: str
    :param check_typ: dApp program type
    :type check_typ: str
    :var filtered_type: filtered dApp program type
    :type filtered_type: str
    :var filtered_name: slugified and filtered dApp provider program name
    :type filtered_name: str
    :return: list generator
    """
    filtered_slug = type_slug
    filtered_name = check_name
    filtered_type = slugify(check_typ)

    if filtered_slug.split("-")[-1].isnumeric():
        filtered_slug = "-".join(filtered_slug.split("-")[:-1])

    if "#" in filtered_name:
        filtered_name = filtered_name.split("#")[0]

    filtered_slug = (
        slugify(filtered_slug)
        .replace("staking", "stake")
        .replace("farming", "farm")
        .replace("staking-reward", "reward")
        .replace("limit", "orders")
        .replace("limit-orders", "orders")
        .replace("added-liquidity", "liquidity")
    )
    filtered_name = (
        slugify(filtered_name)
        .replace("staking", "stake")
        .replace("farming", "farm")
        .replace("staking-reward", "reward")
        .replace("limit-orders", "orders")
        .replace("added-liquidity", "liquidity")
    )
    if filtered_slug == "governance":
        filtered_name = filtered_name.split("#")[0]

    return True if filtered_slug == filtered_type else filtered_slug in filtered_name


def _filter_programs_by_program(program_slug, programs):
    """Filter provided `programs` to include only programs identified by `program`.

    :param program_slug: dApp program slug
    :type program_slug: str
    :param programs: serialized ASA item's programs collection
    :type programs: list
    :return: list
    """
    return [
        program
        for program in programs
        if program.get("program", {}).get("name", "")
        and _check_program_name(
            program_slug, program.get("program", {}).get("name", "")
        )
    ]


def _filter_programs_by_provider(provider, programs):
    """Filter provided `programs` to include only programs from dApp `provider`.

    :param provider: unique dApp provider slug
    :type provider: str
    :param programs: serialized ASA item's programs collection
    :type programs: list
    :return: list
    """
    return [
        program
        for program in programs
        if program.get("program", {}).get("provider", {}).get("name", "")
        and _check_provider_name(
            provider, program.get("program", {}).get("provider", {}).get("name", "")
        )
    ]


def _filter_programs_by_type(program_type, programs):
    """Filter provided `programs` to include only `program_type` programs.

    :param program_type: DeFi program type
    :type program_type: str
    :param programs: serialized ASA item's programs collection
    :type programs: list
    :return: list
    """
    return [
        program
        for program in programs
        if (
            program.get("program", {}).get("name", "")
            or program.get("program", {}).get("type", "")
        )
        and _check_program_type(
            program_type,
            program.get("program", {}).get("name", ""),
            program.get("program", {}).get("type", ""),
        )
    ]


def extract_asaitem(asset_id, asaitems):
    """Return ASA item collection for provided `asset_id` from provided serialized data.

    :param asset_id: Algorand standard asset identifier
    :type asset_id: int
    :param asaitems: serialized evaluated account's ASA items collection
    :type asaitems: dict
    :return: dict
    """
    return next(
        (item for item in asaitems if item.get("asset", {}).get("id") == asset_id), {}
    )


def extract_asaitems_headers(asaitems):
    """Return only ASA item headers from provided ASA items serialized data.

    :param asaitems: serialized evaluated account's ASA items collection
    :type asaitems: dict
    :return: list generator
    """
    return (
        {
            **item,
            **{"programs": []},
            **{"asset": {**item.get("asset"), **{"links": []}}},
        }
        for item in asaitems
    )


def extract_asaitems_program(program, asaitems):
    """Return only ASA item programs defined by `program` slug.

    :param program: dApp program slug
    :type program: str
    :param asaitems: serialized evaluated account's ASA items collection
    :type asaitems: dict
    :return: dict generator
    """
    return (
        item
        for item in (
            {
                **{"asset": {**asaitem.get("asset")}},
                **{
                    "programs": _filter_programs_by_program(
                        program, asaitem.get("programs")
                    )
                },
            }
            for asaitem in asaitems
        )
        if program and len(item.get("programs"))
    )


def extract_asaitems_provider(provider, asaitems):
    """Return only ASA item programs from provided dApp `provider`.

    :param provider: unique dApp provider slug
    :type provider: str
    :param asaitems: serialized evaluated account's ASA items collection
    :type asaitems: dict
    :return: dict generator
    """
    return (
        item
        for item in (
            {
                **{"asset": {**asaitem.get("asset")}},
                **{
                    "programs": _filter_programs_by_provider(
                        provider, asaitem.get("programs")
                    )
                },
            }
            for asaitem in asaitems
        )
        if provider and len(item.get("programs"))
    )


def extract_asaitems_program_type(program_type, asaitems):
    """Return only ASA item programs which type is defined by provided `program_type`.

    :param program_type: DeFi program type
    :type program_type: str
    :param asaitems: serialized evaluated account's ASA items collection
    :type asaitems: dict
    :return: dict generator
    """
    return (
        item
        for item in (
            {
                **{"asset": {**asaitem.get("asset")}},
                **{
                    "programs": _filter_programs_by_type(
                        program_type, asaitem.get("programs")
                    )
                },
            }
            for asaitem in asaitems
        )
        if program_type and len(item.get("programs"))
    )


def _filter_nfts_by_market(market, nfts):
    """Filter provided `nfts` to include only NFTs from provided NFT `market`.

    :param market: unique NFT market slug
    :type market: str
    :param nfts: serialized NFT items collection
    :type nfts: list
    :return: list
    """
    return [
        nft
        for nft in nfts
        if (
            nft.get("nft", {}).get("last_purchase")
            and nft.get("nft").get("last_purchase").get("market", {}).get("name", "")
            and _check_provider_name(
                market,
                nft.get("nft").get("last_purchase").get("market").get("name"),
            )
        )
        or (
            nft.get("nft", {}).get("max_purchase")
            and nft.get("nft").get("max_purchase").get("market", {}).get("name", "")
            and _check_provider_name(
                market,
                nft.get("nft").get("max_purchase").get("market").get("name"),
            )
        )
        or (
            nft.get("nft", {}).get("listings")
            and any(
                listing.get("market", {}).get("name", "")
                and _check_provider_name(market, listing.get("market").get("name"))
                for listing in nft.get("nft", {}).get("listings", [])
            )
        )
        or (
            nft.get("nft", {}).get("floor")
            and any(
                floor.get("market", {}).get("name", "")
                and _check_provider_name(market, floor.get("market").get("name"))
                for floor in nft.get("nft", {}).get("floor", [])
            )
        )
    ]


def _filter_nfts_by_sale_type(sale_type, nfts):
    """Filter provided `nfts` to include only NFTs defined by provided `sale_type`..

    :param sale_type: NFT sale type
    :type sale_type: str
    :param nfts: serialized NFT items collection
    :type nfts: list
    :return: list
    """
    return [
        nft
        for nft in nfts
        if (
            sale_type == "purchase"
            and (
                nft.get("nft", {}).get("last_purchase")
                or nft.get("nft", {}).get("max_purchase")
            )
        )
        or (sale_type == "listing" and nft.get("nft", {}).get("listings"))
        or (sale_type == "floor" and nft.get("nft", {}).get("floor"))
        or (
            sale_type == "no-purchase"
            and (
                not nft.get("nft", {}).get("last_purchase")
                and not nft.get("nft", {}).get("max_purchase")
            )
        )
        or (sale_type == "no-listing" and not nft.get("nft", {}).get("listings"))
        or (sale_type == "no-floor" and not nft.get("nft", {}).get("floor"))
    ]


def extract_nftcollections_headers(nftcollections):
    """Return only NFT collections headers from provided serialized NFT collections.

    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: dict
    :return: list generator
    """
    return (
        {**item, **{"nfts": list(extract_nftitems_headers(item.get("nfts", [])))}}
        for item in nftcollections
    )


def extract_nftcollections_market(market, nftcollections):
    """Return only NFT collections having items from provided NFT `market`.

    :param market: unique NFT market slug
    :type market: str
    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: dict
    :return: dict generator
    """
    return (
        item
        for item in (
            {
                **nftcollection,
                **{"nfts": _filter_nfts_by_market(market, nftcollection.get("nfts"))},
            }
            for nftcollection in nftcollections
        )
        if market and len(item.get("nfts"))
    )


def extract_nftcollections_sale_type(sale_type, nftcollections):
    """Return only NFT collections which sale type is defined by provided `sale_type`.

    :param sale_type: NFT sale type
    :type sale_type: str
    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: dict
    :return: dict generator
    """
    return (
        item
        for item in (
            {
                **nftcollection,
                **{
                    "nfts": _filter_nfts_by_sale_type(
                        sale_type, nftcollection.get("nfts")
                    )
                },
            }
            for nftcollection in nftcollections
        )
        if sale_type and len(item.get("nfts"))
    )


def extract_nftcollection(collection, nftcollections):
    """Return NFT collection item for provided `collection` from provided data.

    :param collection: NFT collection name
    :type collection: str
    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: dict
    :return: dict
    """
    return next(
        (
            nftcollection
            for nftcollection in nftcollections
            if nftcollection.get("name", "") == collection
        ),
        {},
    )


def extract_nftitem(nft_id, nftcollections):
    """Return NFT item for provided `nft_id` from provided serialized data.

    :param nft_id: Algorand standard asset identifier
    :type nft_id: int
    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: dict
    :return: dict
    """
    return next(
        (
            nft
            for nftcollection in nftcollections
            for nft in nftcollection.get("nfts", [])
            if nft.get("nft", {}).get("id") == nft_id
        ),
        {},
    )


def extract_nftitems_from_nftcollections(nftcollections):
    """Return all NFT items from provided serialized NFT collections data.

    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: dict
    :return: dict generator
    """
    return (
        nft for nftcollection in nftcollections for nft in nftcollection.get("nfts", [])
    )


def extract_nftitems_headers(nftitems):
    """Return only NFT items headers from provided serialized NFT items.

    :param nftitems: serialized evaluated account's NFT items
    :type nftitems: dict
    :return: dict generator
    """
    return (
        {
            **item,
            **{
                "nft": {
                    **item.get("nft", {}),
                    **{"urls": None},
                    **{"listings": None},
                    **{"floor": None},
                    **{"last_purchase": None},
                    **{"max_purchase": None},
                    **{"traits": None},
                }
            },
        }
        for item in nftitems
    )


def extract_nftitems_market(market, nftitems):
    """Return only NFT items having entries from provided NFT `market`.

    :param market: unique NFT market slug
    :type market: str
    :param nftitems: serialized evaluated account's NFT items
    :type nftitems: dict
    :return: list
    """
    return _filter_nfts_by_market(market, nftitems)


def extract_nftitems_sale_type(sale_type, nftitems):
    """Return only NFT items which sale type is defined by provided `sale_type`.

    :param sale_type: NFT sale type
    :type sale_type: str
    :param nftitems: serialized evaluated account's NFT items
    :type nftitems: dict
    :return: list
    """
    return _filter_nfts_by_sale_type(sale_type, nftitems)


def _extract_account_markets(nftcollections):
    """Return all NFT markets instances found in provided serialized account's data.

    :param nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: list
    :var markets: collection of NFT market instances
    :type markets: set
    :return: list
    """
    markets = []
    for nft in [
        nft.get("nft", {})
        for nftcollection in nftcollections
        for nft in nftcollection.get("nfts", [])
    ]:
        if nft.get("listings"):
            markets.extend([listing.get("market") for listing in nft.get("listings")])
        if nft.get("floor"):
            markets.extend([listing.get("market") for listing in nft.get("floor")])
        if nft.get("last_purchase"):
            markets.append(nft.get("last_purchase", {}).get("market"))
        if nft.get("max_purchase"):
            markets.append(nft.get("max_purchase", {}).get("market"))

    return _remove_duplicated_dicts_and_sort_by_name(markets)


def _extract_account_programs(asaitems):
    """Return all programs instances found in provided serialized account's data.

    :param asaitems: serialized evaluated account's ASA items collection
    :type asaitems: list
    :return: list
    """
    return _remove_duplicated_dicts_and_sort_by_name(
        [
            {
                key: program.get("program").get(key)
                for key in ("type", "name", "provider")
                if program.get("program").get(key)
            }
            for asaitem in asaitems
            for program in asaitem.get("programs")
        ]
    )


def _extract_account_providers(programs):
    """Return all dApp providers instances found in provided serialized account's data.

    :param programs: collection of dApp programs instances
    :type programs: list
    :return: list
    """
    return _remove_duplicated_dicts_and_sort_by_name(
        [program.get("provider") for program in programs if program.get("provider")]
    )


def _remove_duplicated_dicts_and_sort_by_name(items):
    """Return provided collection of dictionaries sorted by name value.

    :var items: collection of dictionaries
    :type items: list
    :return: list
    """
    return sorted(
        [item for i, item in enumerate(items) if item not in items[i + 1 :]],
        key=lambda x: (x.get("name", ""), x.get("type", "")),
    )


def extract_account_entities(serialized_data):
    """Return all programs, providers and NFT markets instances found in account's data.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :var programs: collection of all dApp programs found in account
    :type programs: list
    :return: dict
    """
    programs = _extract_account_programs(serialized_data.get("asaitems", []))
    return {
        "programs": programs,
        "providers": _extract_account_providers(programs),
        "markets": _extract_account_markets(serialized_data.get("nftcollections", [])),
    }


def extract_account_headers(serialized_data):
    """Return only ASA item and NFT collections headers from provided serialized data.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :return: dict
    """
    return {
        **serialized_data,
        "asaitems": extract_asaitems_headers(serialized_data.get("asaitems")),
        "nftcollections": extract_nftcollections_headers(
            serialized_data.get("nftcollections")
        ),
    }


def extract_top_account_items(serialized_data, limit):
    """Return top valued `limit` number of ASA and/or NFT collections items for account.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param limit: limit number of returned items to this number
    :type limit: str
    :var asaitems: serialized evaluated account's ASA items collection
    :type asaitems: list
    :var nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: list
    :var items: combined ASA and NFT collections items
    :type items: list
    :var boundary: maximum value that shouldn't be included in top items
    :type boundary: float
    :return: dict
    """
    asaitems = serialized_data.get("asaitems", [])
    nftcollections = serialized_data.get("nftcollections", [])
    if len(asaitems) + len(nftcollections) > limit:
        asaitems = asaitems[: int(limit)]
        nftcollections = nftcollections[: int(limit)]
        items = sorted(
            [*asaitems, *nftcollections],
            key=lambda x: float(x.get("value", 0)),
            reverse=True,
        )
        if len(items) > limit:
            boundary = float(items[limit].get("value", 0))
            asaitems = [
                item for item in asaitems if float(item.get("value", 0)) > boundary
            ]
            nftcollections = [
                item
                for item in nftcollections
                if float(item.get("value", 0)) > boundary
            ]

    return {
        "account_info": serialized_data.get("account_info"),
        "total": serialized_data.get("total"),
        "asaitems": asaitems,
        "nftcollections": nftcollections,
    }


def validate_address(value):
    """Raise ValidationError if value isn't a valid public Algorand address.

    :var value: public Algorand address
    :type value: str
    :return: str
    """
    if not value:
        raise ValidationError(INVALID_ADDRESS_INPUT_TEXT)

    if not is_valid_address(value):
        raise ValidationError(INVALID_ADDRESS_TEXT)

    return value


def validate_bundle(value):
    """Return value if it contains a collection of Algorand addresses.

    Raise ValidationError if it doesn't.

    :param value: collection of Algorand addresses or .algo names
    :type value: str
    :var addresses: collection of addresses and .algo names
    :type addresses: str
    :return: str
    """
    if not value:
        raise ValidationError(INVALID_INPUT_TEXT)

    if len(value) == ADDRESS_LEN:
        return validate_address(value)

    addresses = check_bundle_addresses(value)
    if addresses == "":
        raise ValidationError(INVALID_BUNDLE_TEXT)

    return value


def validate_nfd_name(nfd_name):
    """Return bundle or public Algorand address connected with provided NFD name.

    Raise ValidationError if provided value doesn't represent a valid NFD name.

    :param nfd_name: NFD .algo name
    :type nfd_name: str
    :var addresses: collection of public Algorand addresses
    :type addresses: str
    :return: str
    """
    if not nfd_name:
        raise ValidationError(INVALID_NFD_NAME_TEXT)

    addresses = check_algorand_address(nfd_name, raise_error=True)
    if not addresses:
        raise ValidationError(INVALID_NFD_NAME_TEXT)

    return create_bundle(addresses) if " " in addresses else addresses


def validate_raw_addresses(raw):
    """Return collection of public Algorand addresses or single address from `raw`.

    Raise ValidationError if provided value isn't valid.

    :param raw: collection of public Algorand addre4sses and/or NFD .algo names
    :type raw: str
    :var collection: collection of public Algorand addresses
    :type collection: list
    :return: str
    """
    if not raw:
        raise ValidationError(INVALID_RAW_TEXT)

    if len(raw) == ADDRESS_LEN:
        return check_algorand_address(raw, raise_error=True)

    collection = _normalize_collection(_parse_bundle(raw))
    if not collection:
        raise ValidationError(INVALID_RAW_TEXT)

    return " ".join(address for address in set(collection) if address)


def get_lib_doc_excludes():
    """Return list of all classes where docstrings is omitted from API schema.

    :return: list
    """
    return [
        object,
        *[
            getattr(api.serializers, c)
            for c in dir(api.serializers)
            if c.endswith("Serializer")
        ],
    ]


def preprocessing_filter_spec(endpoints):
    """Return list of all endpoint taht should be included in API scheme.

    :var filtered: list of all enpoints to include in schema
    :type filtered: dict
    :return: list
    """
    filtered = []
    for path, path_regex, method, callback in endpoints:
        if path not in ("/api/v2/schema/",):
            filtered.append((path, path_regex, method, callback))
    return filtered
