"""Testing module for :py:mod:`widgethost.manifest` module."""

import pytest

from widgethost.manifest import (
    Manifest,
    ManifestError,
    addresses_limit_for_permission,
    can_access,
    load_manifest,
    required_permission_for_size,
    validate_manifest,
)

HISTORIC_BANDS = [
    {"max_addresses": 1, "permission": 23299689438},
    {"max_addresses": 5, "permission": 258885438200},
    {"max_addresses": 10, "permission": 3236067977500},
]


def valid_manifest_data():
    """Return a minimal valid engine-backed manifest mapping."""
    return {
        "id": "historic",
        "name": "Historic data",
        "version": "0.9.0",
        "origin": "inhouse",
        "capability": "engine-backed",
        "required_permission": 23299689438,
        "engine_endpoints": ["historic:evaluate"],
    }


class TestWidgethostManifestManifest:
    """Testing class for :py:class:`widgethost.manifest.Manifest`."""

    def test_widgethost_manifest_manifest_sets_attributes(self):
        manifest = Manifest(valid_manifest_data())
        assert manifest.id == "historic"
        assert manifest.capability == "engine-backed"
        assert manifest.engine_endpoints == ["historic:evaluate"]

    def test_widgethost_manifest_manifest_applies_defaults(self):
        manifest = Manifest(valid_manifest_data())
        assert manifest.revenue_account == ""
        assert manifest.routes == []
        assert manifest.menu is None
        assert manifest.assets == {}


class TestWidgethostManifestLoadManifest:
    """Testing class for :py:func:`widgethost.manifest.load_manifest`."""

    def test_widgethost_manifest_load_manifest_functionality(self, mocker):
        data = valid_manifest_data()
        mocker.patch("widgethost.manifest.tomllib.load", return_value=data)
        mocker.patch("builtins.open", mocker.mock_open(read_data=b""))
        manifest = load_manifest("/x/widget.toml")
        assert manifest.id == data["id"]


class TestWidgethostManifestValidateManifest:
    """Testing class for :py:func:`widgethost.manifest.validate_manifest`."""

    def test_widgethost_manifest_validate_manifest_for_valid_data(self):
        assert validate_manifest(valid_manifest_data()) is None

    def test_widgethost_manifest_validate_manifest_for_missing_field(self):
        data = valid_manifest_data()
        del data["name"]
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_manifest_for_invalid_origin(self):
        data = valid_manifest_data()
        data["origin"] = "external"
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_manifest_for_invalid_capability(self):
        data = valid_manifest_data()
        data["capability"] = "root"
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_manifest_for_public_with_endpoints(self):
        data = valid_manifest_data()
        data["capability"] = "public"
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_manifest_for_engine_without_endpoints(self):
        data = valid_manifest_data()
        data["engine_endpoints"] = []
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_manifest_for_public_without_endpoints(self):
        data = valid_manifest_data()
        data["capability"] = "public"
        data["engine_endpoints"] = []
        assert validate_manifest(data) is None


class TestWidgethostManifestValidateRequiredPermission:
    """Testing class for the required_permission validation branch."""

    def test_widgethost_manifest_validate_required_permission_for_bool(self):
        data = valid_manifest_data()
        data["required_permission"] = True
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_required_permission_for_empty_list(self):
        data = valid_manifest_data()
        data["required_permission"] = []
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_required_permission_for_bad_band(self):
        data = valid_manifest_data()
        data["required_permission"] = [{"max_addresses": 1}]
        with pytest.raises(ManifestError):
            validate_manifest(data)

    def test_widgethost_manifest_validate_required_permission_for_band_list(self):
        data = valid_manifest_data()
        data["required_permission"] = HISTORIC_BANDS
        assert validate_manifest(data) is None


class TestWidgethostManifestRequiredPermissionForSize:
    """Testing class for :py:func:`widgethost.manifest.required_permission_for_size`."""

    def test_widgethost_manifest_required_permission_for_size_for_integer(self):
        assert required_permission_for_size(500, 99) == 500

    def test_widgethost_manifest_required_permission_for_size_for_first_band(self):
        assert required_permission_for_size(HISTORIC_BANDS, 1) == 23299689438

    def test_widgethost_manifest_required_permission_for_size_for_middle_band(self):
        assert required_permission_for_size(HISTORIC_BANDS, 5) == 258885438200

    def test_widgethost_manifest_required_permission_for_size_over_cap(self):
        assert required_permission_for_size(HISTORIC_BANDS, 11) is None


class TestWidgethostManifestCanAccess:
    """Testing class for :py:func:`widgethost.manifest.can_access`."""

    def test_widgethost_manifest_can_access_over_cap_denies(self):
        assert can_access(10**18, HISTORIC_BANDS, 11) is False

    def test_widgethost_manifest_can_access_for_sufficient_permission(self):
        assert can_access(23299689438, HISTORIC_BANDS, 1) is True

    def test_widgethost_manifest_can_access_for_insufficient_permission(self):
        assert can_access(0, HISTORIC_BANDS, 1) is False


class TestWidgethostManifestAddressesLimitForPermission:
    """Testing class for :py:func:`...manifest.addresses_limit_for_permission`."""

    def test_widgethost_manifest_addresses_limit_for_permission_for_integer(self):
        assert addresses_limit_for_permission(500, 999) == 0

    def test_widgethost_manifest_addresses_limit_for_permission_first_band(self):
        assert addresses_limit_for_permission(HISTORIC_BANDS, 23299689438) == 1

    def test_widgethost_manifest_addresses_limit_for_permission_all_bands(self):
        assert addresses_limit_for_permission(HISTORIC_BANDS, 3236067977500) == 10

    def test_widgethost_manifest_addresses_limit_for_permission_none(self):
        assert addresses_limit_for_permission(HISTORIC_BANDS, 0) == 0
