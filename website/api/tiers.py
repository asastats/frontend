"""What each subscription tier may ask of the API.

**Two axes, and they are not the website's.** The `liverefresh` widget bands how
many addresses a *reader* may watch in a browser - 1 / 1 / 5 / 20 - and those
numbers describe a different product that happens to share the tier names.
Conflating the two is a mistake this project has already made twice, once in the
widget runbook and once in `live/API-TIERS.md`, so the numbers here are written
out rather than imported from there.

    tier          addresses per request
    Asastatser              5
    Professional            5
    Cluster                20

**Addresses per request is the cheap axis.** It bounds a response, not the
engine: five addresses in one call cost one fetch rather than five, which is why
the batched endpoint exists at all. The expensive axis is how many addresses a
subscriber keeps *warm* - under the live pass a warm page is re-priced every
block whether or not anyone reads it - and that is bounded separately where the
subscription is made, not here.

**Freshness is deliberately absent from this table.** Professional and Cluster
are meant to get block-time data, and nothing serves it: the live pass publishes
a diff, and a REST caller holds no state for a diff to apply to - see the gap
recorded in `live/API-TIERS.md`. A `block_time` flag sat here briefly, read by
nothing and asserted by a test, which is how a later change comes to be written
against a promise the code never kept. Freshness lands in this table when
something serves it.
"""

import logging

from django.conf import settings
from rest_framework.exceptions import ValidationError

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

logger = logging.getLogger(__name__)

#: Tier bands, richest first: the first one a permission clears is its own.
#:
#: Below Asastatser there is no band at all - `CanAccessApiPermission` has
#: already refused, or is shadowing a refusal - so a caller reaching these
#: limits has an entitlement by definition.
API_TIER_BANDS = (
    (
        SUBSCRIPTION_TIER_PERMISSIONS["Cluster"],
        {"addresses": 20},
    ),
    (
        SUBSCRIPTION_TIER_PERMISSIONS["Professional"],
        {"addresses": 5},
    ),
    (
        SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"],
        {"addresses": 5},
    ),
)

#: What a caller gets who is past the permission gate but clears no band.
#:
#: Only reachable while the gate is shadowing - an unentitled caller is let
#: through and still has to be given *some* answer. One address is the honest
#: one: they are not paying for a bundle, and shadow mode is meant to show what
#: enforcement would do rather than to hand out entitlements in the meantime.
DEFAULT_BAND = {"addresses": 1}


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


def enforce_address_limit(request, addresses):
    """Refuse a bundle wider than the caller's tier allows - once enforcing.

    **Shadowed on exactly the same switch as the permission gate.** A limit that
    started refusing the moment it was deployed would make `API_TIER_ENFORCED`
    a half-truth: the tier check would be observing while the address check was
    already turning people away, and the log written to answer "who breaks?"
    would be missing the people who had already broken. So while shadowing this
    reports and serves.

    Found by the existing integration tests, which build two- and three-address
    bundles for a caller with no tier and started failing with 400 the moment
    this was added - which is precisely what a real unentitled caller would have
    experienced on deploy day.

    A refusal names both numbers. "Too many addresses" sends a subscriber to a
    support thread; "7 addresses, your tier allows 5" is something they can act
    on without one.

    :param request: DRF request object
    :type request: :class:`rest_framework.request.Request`
    :param addresses: space-joined addresses the bundle resolved to
    :type addresses: str
    :raises ValidationError: when enforcing and the bundle is too wide
    """
    # `request.user` is absent entirely on a bare WSGIRequest - no
    # authentication middleware has run - and a tier limit must not be the thing
    # that turns that into a 500. Absent reads as no entitlement, which the
    # permission gate has already acted on.
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
