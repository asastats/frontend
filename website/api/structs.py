"""Module containing API data structures."""

from collections import namedtuple

AccountInfo = namedtuple(
    "AccountInfo",
    ["addresses", "bundle", "values_in", "online", "points"],
    defaults=[None, None, "ALGO", None, None],
)
Entities = namedtuple(
    "Entities", ["programs", "providers", "markets"], defaults=[None, None, None]
)
AsaItem = namedtuple("AsaItem", ["value", "asset", "amount", "price", "programs"])
AsaItemProgram = namedtuple(
    "AsaItemProgram",
    ["program", "value", "amount", "proxy", "distribution", "linked"],
    defaults=["program", None, None, None, None, None],
)
AsaProgram = namedtuple(
    "AsaProgram",
    ["type", "name", "provider", "url", "code"],
    defaults=[None, None, None, None, None],
)
AsaLink = namedtuple("AsaLink", ["provider", "link", "title"])
Distribution = namedtuple("Distribution", ["value", "amount", "link"])
DistributionLink = namedtuple("DistributionLink", ["provider", "text", "url"])
LinkedData = namedtuple(
    "LinkedData",
    ["provider", "text", "link", "value", "amount", "balance", "info", "id"],
    defaults=[None, "text", None, None, None, None, None, None],
)
Provider = namedtuple("Provider", ["name", "info"], defaults=["Unknown", None])

NftCollection = namedtuple(
    "NftCollection",
    ["value", "name", "amount", "nfts"],  # TODO: "floor" will be added
)
NftItem = namedtuple("NftItem", ["value", "nft", "amount", "price"])
Nft = namedtuple(
    "Nft",
    [
        "id",
        "name",
        "unit",
        "total",
        "decimals",
        "creator",
        "image",
        "thumbnail",
        "urls",
        "listings",
        "floor",  # TODO: will be removed
        "last_purchase",
        "max_purchase",
        "title",
        "description",
        "rarity",
        "traits",
    ],
)
NftCurrency = namedtuple("NftCurrency", ["amount", "asset"])
NftListing = namedtuple("NftListing", ["price", "market", "link", "currency"])
NftPurchase = namedtuple(
    "NftPurchase", ["price", "market", "link", "epoch", "currency"]
)
NftTrait = namedtuple("NftTrait", ["name", "value"])
NftUrl = namedtuple("NftUrl", ["typ", "url"])

SystemInfo = namedtuple("SystemInfo", ["warning", "information"], defaults=[None, None])
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
        "totalwonft",
        "totalwonftusdc",
    ],
)

# # LP
LpProvider = namedtuple("LpProvider", ["code", "name", "baselink"])
LpFarming = namedtuple("LpFarming", ["code", "name", "baselink"])
