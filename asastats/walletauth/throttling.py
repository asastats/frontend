"""Module containing throttling for walletauth app's views."""

from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import UserRateThrottle


class WalletAuthRateThrottle(UserRateThrottle):
    """Per-user throttle for the wallet nonce/verify endpoints.

    The rate is read from ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["walletauth"]``
    (e.g. ``"30/min"``). When that scope is not configured the throttle is inert
    (no limiting) rather than raising, so the endpoints work out of the box and
    operators opt into a limit by setting the rate.

    :var WalletAuthRateThrottle.scope: throttle scope key for the rate lookup
    :type WalletAuthRateThrottle.scope: str
    """

    scope = "walletauth"

    def get_rate(self):
        """Return the configured rate, or ``None`` when the scope is unset.

        :return: rate string such as ``"30/min"``, or None
        :rtype: str | None
        """
        try:
            return super().get_rate()
        except ImproperlyConfigured:
            return None
