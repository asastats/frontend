"""Module containing data structures."""

import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

Asa = namedtuple(
    "Asa", ["id", "name", "unit", "total", "decimals", "url", "creator", "links"]
)
Nft = namedtuple(
    "Nft",
    [
        "id",
        "name",
        "unit",
        "total",
        "collection",  # collection/creator
        "urls",
        "path",
        "tpath",
        "listed",
        "last",
        "max",
        "floor",
        "attrs",
        "title",
        "desc",
        "rarity",
    ],
)
Pool = namedtuple(
    "Pool",
    [
        "app",
        "token",
        "liquidity",
        "asset1",
        "balance1",
        "asset2",
        "balance2",
        "fee",
        "code",
        "address",
        "parent",
    ],
)
Total = namedtuple(
    "Total",
    [
        "algo",
        "asa",
        "nft",
        "total",
        "totalusdc",
        "priceusdc",
        "pricealgo",
        "noteval",
    ],
)
NftPurchase = namedtuple(
    "NftPurchase",
    ["price", "group", "gallery", "time", "currency"],
)
NftListing = namedtuple(
    "NftListing",
    ["asset", "price", "quantity", "gallery", "currency", "app"],
)
NftFloor = namedtuple(
    "NftFloor",
    ["price", "gallery", "currency", "app"],
)
LimitOrder = namedtuple(
    "LimitOrder",
    ["amount_in", "asset_out", "amount_out", "price", "escrow"],
)
Consolidated = namedtuple(
    "Consolidated", ["balance", "staked", "liquidity", "defi", "nftfloor"]
)
LedgerProgram = namedtuple("LedgerProgram", ["asset", "code", "dapp"])
