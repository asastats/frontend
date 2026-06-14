"""Testing module for :py:mod:`walletauth.account_resolution` module."""

import pytest
from django.contrib.auth import get_user_model

from walletauth.account_resolution import (
    AmbiguousWalletAddress,
    resolve_account,
)

user_model = get_user_model()

LINKED_ADDRESS = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


def make_user(username, address="", authorized=""):
    user = user_model.objects.create(username=username)
    user.profile.address = address
    user.profile.authorized = authorized
    user.profile.save()
    return user


class TestResolveAccount:
    """Testing class for :func:`resolve_account`."""

    # # algorand
    @pytest.mark.django_db
    def test_resolve_account_returns_linked_user(self):
        user = make_user("linked", address=LINKED_ADDRESS, authorized="proof")
        assert resolve_account("algorand", LINKED_ADDRESS) == user

    @pytest.mark.django_db
    def test_resolve_account_none_when_address_unverified(self):
        make_user("unverified", address=LINKED_ADDRESS, authorized="")
        assert resolve_account("algorand", LINKED_ADDRESS) is None

    @pytest.mark.django_db
    def test_resolve_account_none_when_no_profile(self):
        assert resolve_account("algorand", LINKED_ADDRESS) is None

    @pytest.mark.django_db
    def test_resolve_account_raises_when_ambiguous(self):
        make_user("a", address=LINKED_ADDRESS, authorized="proof")
        make_user("b", address=LINKED_ADDRESS, authorized="proof")
        with pytest.raises(AmbiguousWalletAddress):
            resolve_account("algorand", LINKED_ADDRESS)

    # # chain routing
    def test_resolve_account_none_for_unsupported_chain(self):
        assert resolve_account("solana", LINKED_ADDRESS) is None

    # # evm (xChain)
    EVM_ADDRESS = "0x52908400098527886e0f7030069857d2e4169ee7"

    @pytest.mark.django_db
    def test_resolve_account_evm_maps_via_check_evm_address(self, mocker):
        user = make_user("evmlinked", address=LINKED_ADDRESS, authorized="proof")
        mocker.patch("utils.clients.algod_instance", return_value=object())
        mocker.patch(
            "nameservice.xchain.check_evm_address", return_value=LINKED_ADDRESS
        )
        assert resolve_account("evm", self.EVM_ADDRESS) == user

    def test_resolve_account_evm_none_when_mapping_fails(self, mocker):
        mocker.patch("utils.clients.algod_instance", return_value=object())
        # check_evm_address echoes the input back on TEAL compile failure
        mocker.patch(
            "nameservice.xchain.check_evm_address", return_value=self.EVM_ADDRESS
        )
        assert resolve_account("evm", self.EVM_ADDRESS) is None

    @pytest.mark.django_db
    def test_resolve_account_evm_raises_when_ambiguous(self, mocker):
        make_user("d1", address=LINKED_ADDRESS, authorized="proof")
        make_user("d2", address=LINKED_ADDRESS, authorized="proof")
        mocker.patch("utils.clients.algod_instance", return_value=object())
        mocker.patch(
            "nameservice.xchain.check_evm_address", return_value=LINKED_ADDRESS
        )
        with pytest.raises(AmbiguousWalletAddress):
            resolve_account("evm", self.EVM_ADDRESS)
