"""Module containing public functions for API v2 package."""

from api.client import fetch_serialized_account
from api.helpers import (
    convert_account_values_to_usd,
    convert_asaitems_values_to_usd,
    convert_items_values_to_usd,
    convert_nftcollections_values_to_usd,
    extract_account_entities,
    extract_account_headers,
    extract_asaitem,
    extract_asaitems_headers,
    extract_asaitems_program,
    extract_asaitems_program_type,
    extract_asaitems_provider,
    extract_nftcollection,
    extract_nftcollections_headers,
    extract_nftcollections_market,
    extract_nftcollections_sale_type,
    extract_nftitem,
    extract_nftitems_from_nftcollections,
    extract_nftitems_headers,
    extract_nftitems_market,
    extract_nftitems_sale_type,
    extract_top_account_items,
)


def account_entities(serialized_data):
    """Return all programs, providers and NFT markets instances found in account's data.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :return: list
    """
    return extract_account_entities(serialized_data)


def fetch_and_serialize_account(bundle, addresses=""):
    """Return the public serialized account schema for ``bundle``.

    :param bundle: single address, or the bundle hash (this app's local id)
    :param addresses: space-joined addresses for a multi-address bundle
    :return: dict
    """
    return fetch_serialized_account(bundle, addresses)


def filtered_asaitem(asset_id, serialized_data, query_params):
    """Return ASA item collection for provided `asset_id` from provided serialized data.

    :param asset_id: Algorand standard asset identifier
    :type asset_id: int
    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param query_params: additional filtering conditions
    :type query_params: :class:`QueryDict`
    :var asaitem: serialized ASA item collection
    :type asaitem: :class:`AsaItem`
    :return: dict
    """
    asaitem = extract_asaitem(asset_id, serialized_data.get("asaitems"))
    return (
        convert_asaitems_values_to_usd(
            [asaitem], serialized_data.get("total").get("pricealgo")
        )[0]
        if query_params.get("usd") in ("true", True)
        else asaitem
    )


def filtered_nftcollection(collection, serialized_data, query_params):
    """Return NFT icollection item for provided `collection` from provided data.

    :param collection: NFT collection name
    :type collection: str
    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param query_params: additional filtering conditions
    :type query_params: :class:`QueryDict`
    :var nftcollection: serialized NFT collection
    :type nftcollection: :class:`NftCollection`
    :return: dict
    """
    nftcollection = extract_nftcollection(
        collection, serialized_data.get("nftcollections")
    )
    return (
        convert_nftcollections_values_to_usd(
            [nftcollection], serialized_data.get("total").get("pricealgo")
        )[0]
        if query_params.get("usd") in ("true", True)
        else nftcollection
    )


def filtered_nftitem(nft_id, serialized_data, query_params):
    """Return NFT item for provided `nft_id` from provided serialized data.

    :param nft_id: Algorand standard asset identifier
    :type nft_id: int
    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param query_params: additional filtering conditions
    :type query_params: :class:`QueryDict`
    :var nftitem: serialized NFT item collection
    :type nftitem: :class:`NftItem`
    :return: dict
    """
    nftitem = extract_nftitem(nft_id, serialized_data.get("nftcollections"))
    return (
        convert_items_values_to_usd(
            [nftitem], serialized_data.get("total").get("pricealgo")
        )[0]
        if query_params.get("usd") in ("true", True)
        else nftitem
    )


def processed_account(serialized_data, query_params):
    """Return processed account data based on values from `query_params`.

    :param serialized_data: serialized evaluated account's data
    :type serialized_data: dict
    :param query_params: additional filtering conditions
    :type query_params: :class:`QueryDict`
    :var limit: limit number of returned ASA items to this number
    :type limit: str
    :return: dict
    """

    limit = query_params.get("limit")
    if limit:
        serialized_data = extract_top_account_items(serialized_data, int(limit))

    if query_params.get("headers") in ("true", True):
        serialized_data = extract_account_headers(serialized_data)

    if query_params.get("usd") in ("true", True):
        serialized_data = convert_account_values_to_usd(
            serialized_data, serialized_data.get("total").get("pricealgo")
        )

    return serialized_data


def processed_asaitems(serialized_data, query_params):
    """Return processed ASA items collection based on values from `query_params`.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param query_params: additional filtering conditions
    :type query_params: :class:`QueryDict`
    :var asaitems: serialized evaluated account's ASA items collection
    :type asaitems: dict
    :var provider: unique dApp provider slug
    :type provider: str
    :var program: unique dApp program slug
    :type program: str
    :var program_type: dApp program type
    :type program_type: str
    :var limit: limit number of returned ASA items to this number
    :type limit: str
    :return: dict
    """
    asaitems = serialized_data.get("asaitems")

    provider = query_params.get("provider")
    if provider:
        asaitems = extract_asaitems_provider(provider, asaitems)

    program = query_params.get("program")
    if program:
        asaitems = extract_asaitems_program(program, asaitems)

    program_type = query_params.get("type")
    if program_type:
        asaitems = extract_asaitems_program_type(program_type, asaitems)

    limit = query_params.get("limit")
    if limit and int(limit):
        asaitems = asaitems[: int(limit)]

    if query_params.get("headers") in ("true", True):
        asaitems = extract_asaitems_headers(asaitems)

    if query_params.get("usd") in ("true", True):
        asaitems = convert_asaitems_values_to_usd(
            asaitems, serialized_data.get("total").get("pricealgo")
        )

    return asaitems


def processed_nftcollections(serialized_data, query_params):
    """Return processed NFT collections based on values from `query_params`.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param query_params: additional filtering conditions
    :type query_params: :class:`QueryDict`
    :var nftcollections: serialized evaluated account's NFT collections
    :type nftcollections: list
    :var market: unique NFT market slug
    :type market: str
    :var sale_type: NFT sale type
    :type sale_type: str
    :var limit: limit number of returned NFT collections to this number
    :type limit: str
    :return: list
    """

    nftcollections = serialized_data.get("nftcollections")

    market = query_params.get("market")
    if market:
        nftcollections = extract_nftcollections_market(market, nftcollections)

    sale_type = query_params.get("type")
    if sale_type:
        nftcollections = extract_nftcollections_sale_type(sale_type, nftcollections)

    limit = query_params.get("limit")
    if limit and int(limit):
        nftcollections = nftcollections[: int(limit)]

    if query_params.get("headers") in ("true", True):
        nftcollections = extract_nftcollections_headers(nftcollections)

    if query_params.get("usd") in ("true", True):
        nftcollections = convert_nftcollections_values_to_usd(
            nftcollections, serialized_data.get("total").get("pricealgo")
        )

    return nftcollections


def processed_nftitems(serialized_data, query_params):
    """Return processed NFT items based on values from `query_params`.

    :param serialized_data: serialized account's data
    :type serialized_data: dict
    :param query_params: additional filtering conditions
    :type query_params: :class:`QueryDict`
    :var nftitems: serialized evaluated account's NFT items
    :type nftitems: dict
    :var market: unique NFT market slug
    :type market: str
    :var sale_type: NFT sale type
    :type sale_type: str
    :var limit: limit number of returned NFT collections to this number
    :type limit: str
    :return: dict
    """
    nftitems = extract_nftitems_from_nftcollections(
        serialized_data.get("nftcollections")
    )

    market = query_params.get("market")
    if market:
        nftitems = extract_nftitems_market(market, nftitems)

    sale_type = query_params.get("type")
    if sale_type:
        nftitems = extract_nftitems_sale_type(sale_type, nftitems)

    if query_params.get("headers") in ("true", True):
        nftitems = extract_nftitems_headers(nftitems)

    nftitems = sorted(nftitems, key=lambda x: float(x.get("value", 0)), reverse=True)

    limit = query_params.get("limit")
    if limit and int(limit):
        nftitems = nftitems[: int(limit)]

    if query_params.get("usd") in ("true", True):
        nftitems = convert_items_values_to_usd(
            nftitems, serialized_data.get("total").get("pricealgo")
        )

    return nftitems
