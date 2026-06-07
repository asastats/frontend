"""Module containing API v2 constants."""

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
)

BASE_API_URL = "https://www.asastats.com/api/v2/"

INVALID_RAW_TEXT = (
    "Collection of public Algorand addresses and/or NFD .algo names is required!"
)
INVALID_ADDRESS_INPUT_TEXT = "Address is required!"
INVALID_INPUT_TEXT = "Bundle or address is required!"
INVALID_NFD_NAME_TEXT = "NFD .algo name is required!"

ACCOUNT_PARAMETERS = [
    # * values in USD
    OpenApiParameter(
        name="usd",
        description="All values in USD.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.BOOL,
        required=False,
    ),
    # * top valued items only
    OpenApiParameter(
        name="limit",
        description=(
            "Return only this number of ASA items and NFT collections "
            "(enter 0 to return only account info and total objects)"
        ),
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.INT,
        required=False,
    ),
    # * Headers only
    OpenApiParameter(
        name="headers",
        description="Return only headers.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.BOOL,
        required=False,
    ),
]

ACCOUNT_ASAS_PARAMETERS = [
    # * dApp provider
    OpenApiParameter(
        name="provider",
        description="Filter by dApp provider.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.STR,
        required=False,
        examples=[
            OpenApiExample(
                name="-",
                description="Return all providers",
                value="",
            ),
            OpenApiExample(
                name="Cometa",
                description="Return only Cometa's staking and farm programs",
                value="cometa",
            ),
            OpenApiExample(
                name="Pact",
                description="Return only Pact's farm and LP contributions",
                value="pact",
            ),
        ],
    ),
    # * dApp provider's program
    OpenApiParameter(
        name="program",
        description="Filter by dApp program.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.STR,
        required=False,
        examples=[
            OpenApiExample(
                name="-",
                description="Return all programs",
                value="",
            ),
            OpenApiExample(
                name="Cometa stake",
                description="Return only Cometa's staking programs",
                value="cometa-stake",
            ),
            OpenApiExample(
                name="Pact farm",
                description="Return only Pact's farms",
                value="pact-farm",
            ),
            OpenApiExample(
                name="Tinyman2 LP",
                description="Return only Tinyman's v2 LP contributions",
                value="tinyman2-lp",
            ),
        ],
    ),
    # * DeFi type (balance/staking/farming/...)
    OpenApiParameter(
        name="type",
        description="Filter by DeFi type.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.STR,
        required=False,
        examples=[
            OpenApiExample(
                name="-",
                description="Return all programs",
                value="",
            ),
            OpenApiExample(
                name="Balance",
                description="Return only ASA balances",
                value="balance",
            ),
            OpenApiExample(
                name="Staking",
                description="Return only staking programs",
                value="staking",
            ),
            OpenApiExample(
                name="Farm",
                description="Return only liquidity pool token farming programs",
                value="farm",
            ),
        ],
    ),
    # * values in USD
    OpenApiParameter(
        name="usd",
        description="All values in USD.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.BOOL,
        required=False,
    ),
    # * ASA items headers only
    OpenApiParameter(
        name="headers",
        description="Return only ASA item headers.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.BOOL,
        required=False,
    ),
    # * top valued items only
    OpenApiParameter(
        name="limit",
        description=(
            "Maximum number of ASA items to return "
            "(leave empty or enter 0 for all records)."
        ),
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.INT,
        required=False,
    ),
]

ACCOUNT_ASAS_ASSET_PARAMETERS = ACCOUNT_ASAS_PARAMETERS[:-1]

ACCOUNT_NFTS_PARAMETERS = [
    # * NFT market
    OpenApiParameter(
        name="market",
        description="Filter by NFT market.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.STR,
        required=False,
        examples=[
            OpenApiExample(
                name="-",
                description="Return all NFT markets/galleries",
                value="",
            ),
            OpenApiExample(
                name="EXA Market 1",
                description="Return only NFTs listed or purchased on EXA Market",
                value="exa-market",
            ),
            OpenApiExample(
                name="EXA Market 2",
                description="Return only NFTs listed or purchased on EXA Market",
                value="exa",
            ),
            OpenApiExample(
                name="Rand Gallery",
                description="Return only NFTs listed or purchased on Rand Gallery",
                value="rand",
            ),
        ],
    ),
    # * values in USD
    OpenApiParameter(
        name="usd",
        description="All values in USD.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.BOOL,
        required=False,
    ),
    # * NFT collections headers only
    OpenApiParameter(
        name="headers",
        description="Return only NFT collection headers.",
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.BOOL,
        required=False,
    ),
    # * top valued items only
    OpenApiParameter(
        name="limit",
        description=(
            "Maximum number of NFT entries to return "
            "(leave empty or enter 0 for all records)."
        ),
        location=OpenApiParameter.QUERY,
        type=OpenApiTypes.INT,
        required=False,
    ),
]

ACCOUNT_NFTS_ASSET_PARAMETERS = ACCOUNT_NFTS_PARAMETERS[:-1]

ADDRESS_DESCRIPTION = (
    "Evaluates provided public Algorand address and returns a collection of "
    "all the ASAs and NFTs owned by the address."
)
BUNDLE_DESCRIPTION = (
    "Evaluates provided bundle hash (collection of public Algorand addresses "
    "and/or NFD .algo names) and returns a collection of all the ASAs and NFTs "
    "owned by addresses in the bundle."
)
NFD_NAME_DESCRIPTION = (
    "Evaluates provided .algo name and returns a collection of "
    "all the ASAs and NFTs owned by the addresses connected to the NFD."
)

_ASAS_DESCRIPTION = "Return provided {0} ASA items."
ADDRESS_ASAS_DESCRIPTION = _ASAS_DESCRIPTION.format("address'")
BUNDLE_ASAS_DESCRIPTION = _ASAS_DESCRIPTION.format("bundle's")
NFD_NAME_ASAS_DESCRIPTION = _ASAS_DESCRIPTION.format(".algo name's")

_ASAS_ASSET_DESCRIPTION = "Return single ASA item for provided {0}."
ADDRESS_ASAS_ASSET_DESCRIPTION = _ASAS_ASSET_DESCRIPTION.format("address")
BUNDLE_ASAS_ASSET_DESCRIPTION = _ASAS_ASSET_DESCRIPTION.format("bundle")
NFD_NAME_ASAS_ASSET_DESCRIPTION = _ASAS_ASSET_DESCRIPTION.format(".algo name")

_NFTS_DESCRIPTION = "Return provided {0} NFT items."
ADDRESS_NFTS_DESCRIPTION = _NFTS_DESCRIPTION.format("address'")
BUNDLE_NFTS_DESCRIPTION = _NFTS_DESCRIPTION.format("bundle's")
NFD_NAME_NFTS_DESCRIPTION = _NFTS_DESCRIPTION.format(".algo name's'")

_NFTS_ASSET_DESCRIPTION = "Return single NFT item for provided {0}."
ADDRESS_NFTS_ASSET_DESCRIPTION = _NFTS_ASSET_DESCRIPTION.format("address")
BUNDLE_NFTS_ASSET_DESCRIPTION = _NFTS_ASSET_DESCRIPTION.format("bundle")
NFD_NAME_NFTS_ASSET_DESCRIPTION = _NFTS_ASSET_DESCRIPTION.format(".algo name")

_NFTCOLLECTIONS_DESCRIPTION = "Return provided {0} NFT collections."
ADDRESS_NFTCOLLECTIONS_DESCRIPTION = _NFTCOLLECTIONS_DESCRIPTION.format("address'")
BUNDLE_NFTCOLLECTIONS_DESCRIPTION = _NFTCOLLECTIONS_DESCRIPTION.format("bundle's")
NFD_NAME_NFTCOLLECTIONS_DESCRIPTION = _NFTCOLLECTIONS_DESCRIPTION.format(".algo name's")

_NFTCOLLECTION_DESCRIPTION = "Return single NFT collection for provided {0}."
ADDRESS_NFTCOLLECTIONS_COLLECTION_DESCRIPTION = _NFTCOLLECTION_DESCRIPTION.format(
    "address"
)
BUNDLE_NFTCOLLECTIONS_COLLECTION_DESCRIPTION = _NFTCOLLECTION_DESCRIPTION.format(
    "bundle"
)
NFD_NAME_NFTCOLLECTIONS_COLLECTION_DESCRIPTION = _NFTCOLLECTION_DESCRIPTION.format(
    ".algo name"
)

_ENTITIES_DESCRIPTION = (
    "Return all dApp program instances, dApp provider instances, "
    "and NFT market instances found in provided {0}."
)
ADDRESS_ENTITIES_DESCRIPTION = _ENTITIES_DESCRIPTION.format("address")
BUNDLE_ENTITIES_DESCRIPTION = _ENTITIES_DESCRIPTION.format("bundle")
NFD_NAME_ENTITIES_DESCRIPTION = _ENTITIES_DESCRIPTION.format(".algo name")

RAW_POST_DESCRIPTION = (
    "Returns a unique bundle hash created from provided addresses and/or NFD .algo "
    "names. Please use spaces, commas, semicolons, underscores or newline characters "
    "to separate addresses/names."
)

SETTINGS_DESCRIPTION = (
    "Return global settings data shared between the website and the mobile "
    "application: ASA and NFT color palettes, the provider-icon path "
    "prefix, and rotating slogans. Mirrors the v1 ``/api/settings/`` "
    "endpoint that this view supersedes; payload shape is identical."
)

SPECTACULAR_DESCRIPTION = (
    r"""By using the ASA Stats API, developers and enthusiasts can """
    r"""create apps and websites that take advantage of all the capabilities offered """
    r"""by the ASA Stats portfolio tracker website.

To whom we aim our services:

* existing projects that want to extend their websites/apps with the additional features
* existing projects that want to focus on new features instead """
    r"""of spending their time and resources on research and development of the new """
    r"""ecosystem providers and/or dApps
* new ecosystem's projects that want to extend their primary functionalities
* new projects that originates completely from the ASA Stats API offering
* companies and hobbists that want to automate their processes

You can get access to our API if you:

* <a href="https://www.asastats.com/subscriptions/">are subscribed</a> """
    r"""to any subscription tier starting from Asastatser
* are an existing <a href="https://github.com/asastats/channel/wiki/Governors">"""
    r"""ASA Stats governor</a>
* have joined our <a href="https://github.com/asastats/channel/discussions/998">"""
    r"""Governance staking program</a> before June, 2024
* <a href="https://github.com/asastats/channel/wiki/GovernorCandidates#description">"""
    r"""have contributed</a> to the ASA Stats project

The following functions and features are included in the API:

__Evaluate any:__

* public Algorand address
* NFD .algo name
* bundle hash (collection of Algorand addresses or .algo names)
* bundle name (coming soon)

__Filter ASA results by:__

* asset identifier
* dApp provider
* dApp provider's program
* DeFi type (balance/staking/farming/...)
* ASA items headers only
* top valued items only

__Filter NFT results by:__

* asset identifier
* NFT collection
* NFT market provider
* NFT market type (listing/purchase/...)
* NFT collections headers only
* top valued items only

__Available formats:__

* JSON
* XML
* YAML

Since we are essentially representing a fully-fledged Algorand portfolio tracker in """
    r"""this stage of the ASA Stats project, all of the API endpoints come from a """
    r"""public Algorand address or a collection of them. Following the deployment """
    r"""of the ASA Stats user widgets system, this API will begin to incorporate """
    r"""additional endpoint types to meet the demands of the ecosystem's users.

Please use our <a href="https://github.com/asastats/channel/issues/new/choose" """
    r"""rel="noopener" title="Go to ASA Stats Channel on GitHub">official channel """
    r"""on GitHub</a> or our community channels to report any errors you've """
    r"""encountered, to suggest additional API endpoints, as well as to provide """
    r"""general feedback.

<a href="/api/v2/schema/swagger-ui/" rel="noopener" """
    r"""title="Swagger UI documentation">Swagger UI documentation</a>&emsp;
<a href="/api/v2/schema/redoc/" rel="noopener" """
    r"""title="Redoc documentation">Redoc documentation</a>

<div><p>Base endpoint: <strong>https://www.asastats.com</strong></p></div>

<div><p><strong>NOTE:</strong> If you haven't already, please create an account """
    r"""and <a href="/profile/api/" rel="noopener" title="Refresh your API token">"""
    r"""refresh your token</a>.</p></div>
"""
)
