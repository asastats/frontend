"""Module containing throttling for walletauth app's views."""

from django.core.exceptions import ImproperlyConfigured
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class _SafeRateMixin:
    """Make an unconfigured scope inert instead of raising ImproperlyConfigured."""

    def get_rate(self):
        """Return the configured rate, or ``None`` when the scope is unset.

        :return: rate string such as ``"30/min"``, or None
        :rtype: str | None
        """
        try:
            return super().get_rate()
        except ImproperlyConfigured:
            return None


class WalletAuthRateThrottle(_SafeRateMixin, UserRateThrottle):
    """Per-user throttle for the wallet nonce/verify (authorize) endpoints.

    The rate is read from ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["walletauth"]``
    (e.g. ``"30/min"``). When that scope is not configured the throttle is inert
    (no limiting) rather than raising, so the endpoints work out of the box and
    operators opt into a limit by setting the rate.

    :var WalletAuthRateThrottle.scope: throttle scope key for the rate lookup
    :type WalletAuthRateThrottle.scope: str
    """

    scope = "walletauth"


class WalletLoginRateThrottle(_SafeRateMixin, AnonRateThrottle):
    """Per-IP throttle for the unauthenticated wallet sign-in endpoints.

    Sign-in is anonymous, so the limit is keyed by client IP. Configure
    ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["walletauth-login"]``
    (e.g. ``"10/min"``); inert until set.

    :var WalletLoginRateThrottle.scope: throttle scope key for the rate lookup
    :type WalletLoginRateThrottle.scope: str
    """

    scope = "walletauth-login"
