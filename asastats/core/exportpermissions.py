"""Size-scaled tier gate shared by the browsing user (Gate B) and the deployment (Gate A).

Permission is a single integer (on-chain for users; returned by the backend
capabilities endpoint for the deployment) compared against tier thresholds, with
the required tier rising as the bundle's address count grows.
"""

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

# Max bundle size each tier may export. Mirrors the historic widget's limits;
# adjust per business rules.
EXPORT_TIERS_ADDRESSES_LIMIT = {
    "Intro": 0,
    "Asastatser": 1,
    "Professional": 5,
    "Cluster": 10,
}


def tier_allows(permission_value, size, limits=EXPORT_TIERS_ADDRESSES_LIMIT):
    """Return True if ``permission_value`` is entitled to export a bundle of ``size``.

    :param permission_value: integer permission (user's or the deployment's)
    :param size: number of Algorand addresses in the bundle
    :return: bool
    """
    if permission_value is None or size > limits["Cluster"]:
        return False
    if size > limits["Professional"]:
        return permission_value >= SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]
    if size > limits["Asastatser"]:
        return permission_value >= SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
    return permission_value >= SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
