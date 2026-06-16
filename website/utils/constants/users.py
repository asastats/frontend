"""Module containing constants related to user authentication system."""

from collections import namedtuple

BundleLimit = namedtuple("BundleLimit", ["count", "size"])

PERMISSION_APP_ID = 2685515413
PERMISSION_VALUE_START = 16

SUBSCRIPTION_TIER_PERMISSIONS = {
    "Intro": 2_329_968_943,
    "Asastatser": 23_299_689_438,
    "Professional": 258_885_438_200,
    "Cluster": 3_236_067_977_500,
}

SUBSCRIPTION_TIER_BUNDLE_NAMES_COUNT = {
    "Trial": (BundleLimit(0, 5),),
    "Intro": (BundleLimit(3, 8),),
    "Asastatser": (BundleLimit(3, 15), BundleLimit(5, 10)),
    "Professional": (BundleLimit(3, 35), BundleLimit(5, 15), BundleLimit(10, 10)),
    "Cluster": (
        BundleLimit(3, 100),
        BundleLimit(5, 35),
        BundleLimit(10, 15),
        BundleLimit(20, 10),
    ),
}

SUBSCRIPTION_TIER_PUBLIC_BUNDLE_NAMES_COUNT = {
    "Trial": (BundleLimit(0, 0),),
    "Intro": (BundleLimit(0, 0),),
    "Asastatser": (BundleLimit(0, 10), BundleLimit(1, 8)),
    "Professional": (BundleLimit(0, 15), BundleLimit(1, 10), BundleLimit(2, 8)),
    "Cluster": (
        BundleLimit(0, 35),
        BundleLimit(1, 15),
        BundleLimit(2, 10),
        BundleLimit(2, 8),
    ),
}

MANDATORY_VALUES_SIZE = 48

BUNDLENAME_REGEX = r"([-a-zA-Z0-9_\.]{1,50})"

HASHIDS_SALT = "YKmvVHqkEh"

ADMPOOL_ADDRESS = "E7TR4BUASOGSHRRE2IBUHTHSNZGKU2DQDU5UF77L7VBITNVQGW5SCMS7OI"
ADMPOOL_AUTHORIZATION_MIN_ROUND = 45500000

TOO_LONG_USER_FIRST_NAME_ERROR = "User name is limited to 30 characters only"
TOO_LONG_USER_LAST_NAME_ERROR = "User last name is limited to 150 characters only"

TOO_LONG_BUNDLE_NAME_ERROR = "Bundle name should contain no more than 50 characters"
TOO_LONG_BUNDLE_ADDRESSES_ERROR = "Too long addresses field"

DUPLICATE_BUNDLE_NAME_ERROR = "You've already have got this bundle name"
DUPLICATE_BUNDLE_ERROR = "You've already have got such a bundle"

REQUIRED_BUNDLE_NAME_ERROR = "This field is required"
REQUIRED_BUNDLE_ADDRESSES_ERROR = "A public Algorand address is required"

DUPLICATE_PUBLIC_BUNDLE_NAME_ERROR = "This bundle name is occupied"
BUNDLE_ADDRESSES_LIMIT_HELP_TEXT = "Maximum number of addresses in a bundle is {}.<br>"
PUBLIC_BUNDLE_ADDRESSES_LIMIT_HELP_TEXT = (
    "Maximum number of addresses in a public bundle is {}."
)
PUBLIC_BUNDLE_ADDRESSES_NOT_ALLOWED_HELP_TEXT = (
    "Your subscription tier doesn't allow creating a new public bundle."
)

BUNDLE_NAME_NOT_FOUND_ERROR = "Bundle name not found!"

BUNDLE_NAME_DELETED_MESSAGE = "Bundle name has been deleted"

ADJUST_BUNDLE_NAMES_SIZE_ERROR = (
    "Decrease number of bundle names and/or their size to fit your "
    "<a href='/subscriptions/' target='_blank' rel='noopener'>subscription tier</a>."
)
AUTHORIZATION_TRANSACTION_CONFIRMED_MESSAGE = "Address is authorized!"
AUTHORIZATION_TRANSACTION_ERROR_MESSAGE = (
    "Authorization transaction to our escrow not found!"
)

SYSTEM_RESERVED_URL_PATH_ERROR = "The name is a reserved system URL"
ADDRESS_AND_ALGO_NAME_URL_PATH_ERROR = (
    "NFDomains .algo names are not allowed as bundle names"
)

BUNDLENAME_PUBLIC_HELP_TEXT = (
    "Make bundle name unique and publicly accessible by anyone"
)
