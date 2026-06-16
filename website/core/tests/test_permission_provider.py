"""Testing module for :py:mod:`core.permission_provider` module."""

from django.test import override_settings

from core.permission_provider import (
    PermissionProvider,
    get_permission_provider,
)


class _StubProvider(PermissionProvider):
    """Stub provider used to verify settings-based resolution."""

    def votes_and_permission(self, address):
        """Return a fixed pair.

        :param address: public Algorand address
        :type address: str
        :return: two-tuple
        """
        return (1, 2)


class TestCorePermissionProviderPermissionProvider:
    """Testing class for :py:class:`core.permission_provider.PermissionProvider`."""

    def test_core_permission_provider_votes_and_permission_default(self):
        assert PermissionProvider().votes_and_permission("ADDRESS") is None

    def test_core_permission_provider_subscriptions_default(self):
        assert PermissionProvider().subscriptions("ADDRESS") is None

    def test_core_permission_provider_refresh_default(self):
        assert PermissionProvider().refresh() is None

    def test_core_permission_provider_tier_link_default(self):
        assert PermissionProvider().tier_link("Cluster") == "Cluster"


class TestCorePermissionProviderGetPermissionProvider:
    """Testing class for :py:func:`...permission_provider.get_permission_provider`."""

    @override_settings(PERMISSION_PROVIDER=None)
    def test_core_permission_provider_get_provider_default(self):
        assert type(get_permission_provider()) is PermissionProvider

    @override_settings(
        PERMISSION_PROVIDER="core.tests.test_permission_provider._StubProvider"
    )
    def test_core_permission_provider_get_provider_configured(self):
        provider = get_permission_provider()
        assert isinstance(provider, _StubProvider)
        assert provider.votes_and_permission("ADDRESS") == (1, 2)
