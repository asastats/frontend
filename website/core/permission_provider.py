"""Pluggable permission backend for the open frontend.

The frontend depends only on this abstraction. The ASA Stats on-chain
implementation (or any deployer's alternative) is named by the
``PERMISSION_PROVIDER`` setting and resolved lazily, so the open repo imports no
deployment-specific code and boots even when that backend is not installed.
"""

from functools import lru_cache

from django.conf import settings
from django.dispatch import receiver
from django.test.signals import setting_changed
from django.utils.module_loading import import_string


class PermissionProvider:
    """Default no-op permission backend.

    Deployers subclass this and point ``settings.PERMISSION_PROVIDER`` at their
    subclass to plug in a real backend. Every method degrades safely so a
    deployment with no provider keeps working and never has user data reset.
    """

    def votes_and_permission(self, address):
        """Return the votes and permission pair for an address.

        :param address: public Algorand address
        :type address: str
        :return: two-tuple of ints, or None to leave the profile unchanged
        """
        return None

    def subscriptions(self, address):
        """Return render-ready subscription data for the profile page.

        :param address: public Algorand address
        :type address: str
        :return: render-ready collection, or None when there is nothing to show
        """
        return None

    def refresh(self):
        """Run the periodic permission-backend update. No-op by default.

        :return: None
        """

    def tier_link(self, tier_name):
        """Return display markup for a subscription tier name.

        :param tier_name: subscription tier name
        :type tier_name: str
        :return: str
        """
        return tier_name


@lru_cache(maxsize=1)
def get_permission_provider():
    """Return the configured permission provider instance, built once.

    Resolves ``settings.PERMISSION_PROVIDER`` lazily on first call, so the
    frontend imports no deployment-specific module unless one is configured.

    :var dotted: dotted path to the provider class, or None
    :type dotted: str
    :return: :class:`PermissionProvider`
    """
    dotted = getattr(settings, "PERMISSION_PROVIDER", None)
    if not dotted:
        return PermissionProvider()

    return import_string(dotted)()


@receiver(setting_changed)
def _reset_permission_provider_cache(*, setting, **kwargs):
    """Clear the cached provider when its setting changes, e.g. in tests.

    :param setting: name of the changed setting
    :type setting: str
    :return: None
    """
    if setting == "PERMISSION_PROVIDER":
        get_permission_provider.cache_clear()
