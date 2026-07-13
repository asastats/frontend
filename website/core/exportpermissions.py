"""Size-scaled tier gate shared by the browsing user (Gate B) and the deployment (Gate A).

Permission is a single integer (on-chain for users; returned by the backend
capabilities endpoint for the deployment) compared against tier thresholds, with
the required tier rising as the bundle's address count grows.
"""

from django.conf import settings

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

_DEFAULT_LIMITS = {
    "free": 0,
    "Intro": 0,
    "Asastatser": 0,
    "Professional": 0,
    "Cluster": 5,
}


def _export_limits():
    """Active address-count limits: deployment override merged over defaults."""
    override = getattr(settings, "EXPORT_TIERS_ADDRESSES_LIMIT", None) or {}
    return {**_DEFAULT_LIMITS, **override}


def tier_allows(permission_value, size, limits=None):
    """Return True if ``permission_value`` may export a bundle of ``size``.

    Free (no-tier) users may export up to the ``free`` limit; paid tiers extend
    it. ``permission_value`` is ``None`` for a no-tier user, which is allowed
    within the free range and rejected beyond it.

    :param permission_value: integer permission (user's or deployment's) or None
    :param size: number of Algorand addresses in the bundle
    :param limits: address-count limits per tier; resolved from settings if None
    :return: bool
    """
    limits = limits or _export_limits()
    if size > limits["Cluster"]:
        return False

    if size <= limits["free"]:
        return True

    permission_value = permission_value or 0
    if size > limits["Professional"]:
        return permission_value >= SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]

    if size > limits["Asastatser"]:
        return permission_value >= SUBSCRIPTION_TIER_PERMISSIONS["Professional"]

    if size > limits["Intro"]:
        return permission_value >= SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]

    return permission_value >= SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
