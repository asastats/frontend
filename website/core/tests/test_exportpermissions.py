"""Testing module for :py:mod:`core.exportpermissions` module."""

from core.exportpermissions import tier_allows
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


class TestCoreExportPermissionsTierAllows:
    """Testing class for :py:func:`core.exportpermissions.tier_allows`."""

    def test_core_exportpermissions_tier_allows_returns_false_for_no_permission(self):
        assert tier_allows(None, 1) is False

    def test_core_exportpermissions_tier_allows_returns_false_for_oversized(self):
        assert tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 11) is False

    def test_core_exportpermissions_tier_allows_for_cluster_sized_bundle(self):
        assert tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 6) is True
        assert tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Cluster"] - 1, 6) is False

    def test_core_exportpermissions_tier_allows_for_professional_sized_bundle(self):
        assert tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 2) is True
        assert tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 2) is False

    def test_core_exportpermissions_tier_allows_for_single_address(self):
        assert tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 1) is True
        assert tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 1) is False
