"""Module containing core app's constants."""

from http.client import RemoteDisconnected
from urllib.error import HTTPError, URLError

from algosdk.error import (
    AlgodHTTPError,
    AlgodResponseError,
    AtomicTransactionComposerError,
)

ALGORAND_BLOCK_SPEED = 3.7

ACCOUNT_INFO_SIZE_LIMIT = 1000000
ACCOUNT_INFO_ASSETS_LIMIT = 100000
REDUCED_ACCOUNT_ASSETS_SIZE = 1000
REDUCED_ACCOUNT_WARNING_MESSAGE = "Reduced account data!"

CACHE_TTL_ADDRESS = 60  # cache address page for this much seconds
CACHE_TTL_CUSTOM_ADDRESS = 900

ALGO_ID = 0
USDC_ID = 31566704
USDT_ID = 312769
ASASTATS_ID = 393537671
FAILBACK_USDC_PRICE = 10.363
FAILBACK_ASASTATS_PRICE = 0.00037
DEFAULT_SLEEP_INTERVAL = 1

ASASTATS_SLOGANS = (
    "All your Algorand assets on one dashboard",
    "Your entire Algorand portfolio in one place",
    "The maximum value of your assets aggregated using the entire ecosystem liquidity",
)

BANNERS = [
    # {
    #     "image": "img/xgov-rewards-suite-banner1.jpg",
    #     "url": (
    #         "https://forum.algorand.co/t/the-rewards-suite-all-in-one-"
    #         "infrastructure-for-transparent-contributor-rewards-"
    #         "by-asa-stats/15243"
    #     ),
    #     "alt": "Join the the Rewards Suite xGov proposal discussion on Algorand Forum",
    #     "weight": 1,
    # },
    # {
    #     "image": "img/xgov-voting-rewards-suite-banner.jpg",
    #     "url": "https://xgov.algorand.co/proposal/3512192654",
    #     "alt": "Vote on the Rewards Suite xGov proposal on the xGov platform",
    #     "weight": 1,
    # },
]

ASASTATS_API_UNIT_PRICE_ENDPOINT = "https://www.asastats.com/api/unit-price/"

# # SETTINGS ERRORS
MISSING_ENVIRONMENT_VARIABLE_ERROR = "Environment variable is not set"

CONTENT_TYPES_FOR_EXTENSION = {
    ".zip": "application/x-zip-compressed",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
}

INVALID_ADDRESS_TEXT = "Invalid Algorand address!"

BUNDLE_SEPARATION_CHARS = (" ", ",", ";", "_")
MAX_BUNDLE_SIZE = 5

MAX_VALUE_FRAGMENT_LIMIT = 2  # percentage
MAX_VALUE_FRAGMENT_BOUND = 2  # percentage
MAX_VALUE_CONCLUSION = 10  # percentage
MAX_VALUE_USE_HUNDREDTHS = True
MAX_VALUE_SKIP_POOL_PERCENTAGE = 0.1

ASC_DUST_LIMIT = 0.001

MISSING_RAW_TEXT = "'raw' object is missing!"
INVALID_BUNDLE_TEXT = "Bundle doesn't exist!"
MISSING_ASSET_TEXT = "'asset' object is missing!"

ALGOD_EXCEPTIONS = (
    AlgodHTTPError,
    AlgodResponseError,
    AtomicTransactionComposerError,
    HTTPError,
    URLError,
    ConnectionResetError,
    RemoteDisconnected,
    TimeoutError,
)
ALGOD_ASSET_ERROR_TEXT = "asset does not exist"
ALGOD_APP_ERROR_TEXT = "application does not exist"
ALGOD_BOX_ERROR_TEXT = "box not found"

DISASSEMBLE_ENDPOINT = "/teal/disassemble"

EPOCH_IN_FUTURE = 2000000000
SECONDS_IN_YEAR = 365 * 24 * 60 * 60

TRANSMITTER_TIMEOUT = 60
UPDATERNFT_TIMEOUT = 1800
APIUPDATERNFT_TIMEOUT = 30
QUARTER = 0.72
PERMISSIONS_TTL = 40 * QUARTER

# FORBIDDEN_ADDRESSES = ["MVEKYHFLJ63UKDYGNKCJD7WO5KFJZFVFMJPSDAWLDIDP4LUP575YDOW6GI"]
FORBIDDEN_ADDRESSES = [
    "OMXLQTI5ZSMWTCIZA3O3YBW74BTCOI67SZTOEDHK3ZEDZ34Z3DEOQD4PW4",  # NFD escrow
]

BLANK_ADDRESS = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"

REQUESTS_USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0",
]

ELEMENTS_STYLING = {
    "login": {"icon": "account_circle"},
    "password": {"icon": "lock"},
    "email": {"icon": "mail"},
    "password1": {"icon": "lock"},
    "password2": {"icon": "lock"},
    "oldpassword": {"icon": "lock_open"},
    "help": {"icon": "help"},
    "home": {"icon": "home"},
    "auth_action": {"icon": "verified_user"},
    "auth_help": {"icon": "help_outline"},
    "cancel": {"icon": "highlight_off"},
    "add": {"icon": "library_add"},
    "save": {"icon": "save"},
    "menu": {"icon": "menu"},
    "logout": {"icon": "exit_to_app"},
    "edit": {"icon": "perm_identity"},
    "cta": {"icon": "call_to_action"},
    "close": {"icon": "close"},
    "editor": {"icon": "dashboard"},
    "template": {"icon": "library_books"},
    "reveal": {"icon": "more_vert"},
    "website": {"icon": "web"},
    "submit": {"icon": "send"},
    "add_circle": {"icon": "add_circle"},
    "remove": {"icon": "remove_circle"},
    "social": {"icon": "account_box"},
    "deactivate": {"icon": "do_not_disturb_alt"},
    "config": {"icon": "settings"},
    "history": {"icon": "history"},
    "upload": {"icon": "file_upload"},
    "import": {"icon": "cached"},
    "wizard": {"icon": "dynamic_feed"},
    "yes": {"icon": "check"},
    "first": {"icon": "first_page"},
    "prev": {"icon": "chevron_left"},
    "render": {"icon": "print"},
    "subscribe": {"icon": "account_balance_wallet"},
    "account": {"icon": "account_box"},
    "api": {"icon": "api"},
    "refresh": {"icon": "refresh"},
    "fingerprint": {"icon": "fingerprint"},
    "public": {"icon": "public"},
}

DEPRECATED_LINK_PROVIDERS = ["cmc"]
