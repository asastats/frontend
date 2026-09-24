"""What each subscription tier may ask of the API.

    tier          addresses per request
    Asastatser              5
    Professional            5
    Cluster                20

**These are not the `liverefresh` widget's bands.** That widget limits how many
addresses a *reader* may watch in a browser, 1 / 1 / 5 / 20, and it is a
different product that happens to share the tier names. The numbers here are
written out rather than imported from there.

Addresses per request bounds a response, not the engine: five addresses in one
call cost one fetch rather than five, which is why the batched endpoint exists.
How many addresses a subscriber keeps *warm* is the expensive axis, and it is
bounded where the subscription is made rather than here.

`block_time` is read by `api.live.wants_block_time`, and this is the one place
that decides which tiers get it.
"""

import logging

from django.conf import settings
from rest_framework.exceptions import ValidationError

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

logger = logging.getLogger(__name__)

#: Tier bands, richest first: the first one a permission clears is its own.
#: Below Asastatser there is no band, because `CanAccessApiPermission` has
#: already refused or is shadowing a refusal.
API_TIER_BANDS = (
    (
        SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
        {"addresses": 20, "block_time": True},
    ),
    (
        SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
        {"addresses": 5, "block_time": True},
    ),
    (
        SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
        # Five addresses, on the 60-second cached path. Freshness is
        # Professional's whole advantage over this tier.
        {"addresses": 5, "block_time": False},
    ),
)

#: What a caller gets who is past the permission gate but clears no band.
#: Reachable only while the gate is shadowing, and one address is the honest
#: answer: they are not paying for a bundle.
DEFAULT_BAND = {"addresses": 1, "block_time": False}


def band_for(permission):
    """Return the API band `permission` falls in.

    :param permission: the caller's permission integer
    :type permission: int
    :return: dict
    """
    for required, band in API_TIER_BANDS:
        if permission >= required:
            return band
    return DEFAULT_BAND


def max_addresses(permission):
    """Return how many addresses `permission` may ask about in one request.

    :param permission: the caller's permission integer
    :type permission: int
    :return: int
    """
    return band_for(permission)["addresses"]


def block_time(permission):
    """Return whether `permission` includes block-time data.

    :param permission: the caller's permission integer
    :type permission: int
    :return: bool
    """
    return band_for(permission).get("block_time", False)


def enforce_address_limit(request, addresses):
    """Refuse a bundle wider than the caller's tier allows - once enforcing.

    **Shadowed on the same switch as the permission gate.** A limit refusing
    while the tier check only observes would make `API_TIER_ENFORCED` a
    half-truth, and the log written to answer "who breaks?" would be missing
    the people who had already broken. So while shadowing this reports and
    serves.

    A refusal names both numbers, so a subscriber can act on it without opening
    a support thread.

    :param request: DRF request object
    :type request: :class:`rest_framework.request.Request`
    :param addresses: space-joined addresses the bundle resolved to
    :type addresses: str
    :raises ValidationError: when enforcing and the bundle is too wide
    """
    # `request.user` is absent on a bare WSGIRequest, and a tier limit must not
    # be what turns that into a 500. Absent reads as no entitlement.
    user = getattr(request, "user", None)
    profile = getattr(user, "profile", None)
    allowed = max_addresses(getattr(profile, "permission", 0) or 0)
    asked = len(addresses.split())
    if asked <= allowed:
        return

    if not getattr(settings, "API_TIER_ENFORCED", False):
        logger.warning(
            "api tier shadow: would refuse %s addresses (allows %s) "
            "user=%s permission=%s path=%s",
            asked,
            allowed,
            getattr(user, "pk", None),
            getattr(profile, "permission", None),
            getattr(request, "path", None),
        )
        return

    raise ValidationError(
        f"This bundle has {asked} addresses and your subscription allows "
        f"{allowed} per request."
    )
