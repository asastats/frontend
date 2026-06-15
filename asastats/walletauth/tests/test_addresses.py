"""Testing module for :py:mod:`walletauth.addresses` module."""

import pytest
from django.test import override_settings

from walletauth.addresses import (
    CanonicalizationError,
    canonical_for,
    max_secondary_addresses,
)

ALGO = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
EVM = "0x52908400098527886e0f7030069857d2e4169ee7"
LSIG = "LSIG7NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34ABCD"


class TestCanonicalFor:
    """Testing class for :func:`canonical_for`."""

    # # native
    def test_canonical_for_native_returns_address_unchanged(self):
        # No algod call for native (the harness algod_instance raises if used).
        assert canonical_for("algorand", ALGO) == ALGO

    # # evm
    def test_canonical_for_evm_returns_lsig_counterpart(self, mocker):
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        mocker.patch("walletauth.addresses.check_evm_address", return_value=LSIG)
        assert canonical_for("evm", EVM) == LSIG

    def test_canonical_for_evm_raises_when_unresolvable(self, mocker):
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        # Failure path: check_evm_address returns its input unchanged.
        mocker.patch("walletauth.addresses.check_evm_address", return_value=EVM)
        with pytest.raises(CanonicalizationError):
            canonical_for("evm", EVM)


class TestMaxSecondaryAddresses:
    """Testing class for :func:`max_secondary_addresses`."""

    def test_max_secondary_addresses_default(self):
        assert max_secondary_addresses() == 10

    @override_settings(MAX_SECONDARY_ADDRESSES=3)
    def test_max_secondary_addresses_setting_override(self):
        assert max_secondary_addresses() == 3
