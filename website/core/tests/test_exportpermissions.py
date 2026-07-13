"""Testing module for :py:mod:`core.exportpermissions` module."""

from core.exportpermissions import tier_allows, _export_limits, _DEFAULT_LIMITS
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


class TestCoreExportPermissionsExportLimits:
    """Testing class for :py:func:`core.exportpermissions._export_limits`."""

    def test_export_limits_returns_defaults_when_setting_none(self, mocker):
        mocker.patch("core.exportpermissions.getattr", return_value=None)
        assert _export_limits() == _DEFAULT_LIMITS

    def test_export_limits_returns_merged_dictionary_with_overrides(self, mocker):
        override = {"free": 10, "CustomTier": 99}
        mocker.patch("core.exportpermissions.getattr", return_value=override)
        expected = {**_DEFAULT_LIMITS, **override}
        assert _export_limits() == expected


class TestCoreExportPermissionsTierAllows:
    """Testing class for :py:func:`core.exportpermissions.tier_allows`."""

    def test_tier_allows_resolves_default_limits_if_none_provided(self, mocker):
        mocked_export_limits = mocker.patch(
            "core.exportpermissions._export_limits",
            return_value={"Cluster": 5, "free": 1},
        )
        # Size 6 exceeds Cluster limit of 5, triggering early False return
        assert tier_allows(None, 6) is False
        mocked_export_limits.assert_called_once_with()

    def test_tier_allows_returns_false_for_oversized_bundle(self):
        limits = {"Cluster": 5}
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 6, limits=limits)
            is False
        )

    def test_tier_allows_returns_true_for_free_size(self):
        limits = {"Cluster": 5, "free": 2}
        # Even with None permission, size <= free returns True
        assert tier_allows(None, 2, limits=limits) is True

    def test_tier_allows_checks_cluster_permission_for_size_over_professional(self):
        limits = {"Cluster": 5, "free": 0, "Professional": 3}
        # Size 4 > Professional (3)
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Cluster"], 4, limits=limits)
            is True
        )
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 4, limits=limits)
            is False
        )

    def test_tier_allows_checks_professional_permission_for_size_over_asastatser(self):
        limits = {"Cluster": 5, "free": 0, "Professional": 4, "Asastatser": 2}
        # Size 3 > Asastatser (2)
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Professional"], 3, limits=limits)
            is True
        )
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 3, limits=limits)
            is False
        )

    def test_tier_allows_checks_asastatser_permission_for_size_over_intro(self):
        limits = {
            "Cluster": 5,
            "free": 0,
            "Professional": 4,
            "Asastatser": 3,
            "Intro": 1,
        }
        # Size 2 > Intro (1)
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], 2, limits=limits)
            is True
        )
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 2, limits=limits)
            is False
        )

    def test_tier_allows_checks_intro_permission_for_size_under_intro_but_over_free(
        self,
    ):
        limits = {
            "Cluster": 5,
            "free": 0,
            "Professional": 4,
            "Asastatser": 3,
            "Intro": 2,
        }
        # Size 1 <= Intro (2), but > free (0) -> falls through to the final return
        assert (
            tier_allows(SUBSCRIPTION_TIER_PERMISSIONS["Intro"], 1, limits=limits)
            is True
        )
        # Tests the 'permission_value = permission_value or 0' fallback logic
        assert tier_allows(None, 1, limits=limits) is False
