"""Testing module for :py:mod:`walletauth.account_resolution` module."""

import pytest
from django.contrib.auth import get_user_model

from walletauth.account_resolution import (
    AmbiguousWalletAddress,
    resolve_account,
)
from walletauth.models import LinkedAddress

user_model = get_user_model()

ALGO = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
EVM = "0x52908400098527886e0f7030069857d2e4169ee7"


def link(username, address, *, login_enabled=True, is_primary=True):
    user = user_model.objects.create(username=username)
    LinkedAddress.objects.create(
        profile=user.profile,
        address=address,
        canonical_address=address,
        chain="evm" if address.startswith("0x") else "algorand",
        auth_method="evm_xchain" if address.startswith("0x") else "algorand_wallet",
        is_primary=is_primary,
        login_enabled=login_enabled,
    )
    return user


class TestResolveAccount:
    """Testing class for :func:`resolve_account`."""

    # # primary / login-enabled
    @pytest.mark.django_db
    def test_resolve_account_returns_user_for_login_enabled_primary(self):
        user = link("primary", ALGO, is_primary=True, login_enabled=True)
        assert resolve_account("algorand", ALGO) == user

    @pytest.mark.django_db
    def test_resolve_account_returns_user_for_opted_in_secondary(self):
        user = link("sec", ALGO, is_primary=False, login_enabled=True)
        assert resolve_account("algorand", ALGO) == user

    # # the opt-in gate
    @pytest.mark.django_db
    def test_resolve_account_none_for_secondary_without_login_enabled(self):
        link("optout", ALGO, is_primary=False, login_enabled=False)
        assert resolve_account("algorand", ALGO) is None

    @pytest.mark.django_db
    def test_resolve_account_none_when_unlinked(self):
        assert resolve_account("algorand", ALGO) is None

    # # chain routing
    def test_resolve_account_none_for_unsupported_chain(self):
        assert resolve_account("solana", ALGO) is None

    # # ambiguity (defensive: the canonical unique constraint prevents it)
    @pytest.mark.django_db
    def test_resolve_account_raises_when_ambiguous(self, mocker):
        queryset = mocker.MagicMock()
        queryset.get.side_effect = LinkedAddress.MultipleObjectsReturned
        mocker.patch.object(
            LinkedAddress.objects, "select_related", return_value=queryset
        )
        with pytest.raises(AmbiguousWalletAddress):
            resolve_account("algorand", ALGO)

    # # evm (xChain): resolved by the stored 0x address, no algod mapping
    @pytest.mark.django_db
    def test_resolve_account_evm_resolves_by_stored_address(self):
        user = link("evm", EVM, is_primary=False, login_enabled=True)
        assert resolve_account("evm", EVM) == user

    @pytest.mark.django_db
    def test_resolve_account_evm_none_when_not_login_enabled(self):
        link("evmoptout", EVM, is_primary=False, login_enabled=False)
        assert resolve_account("evm", EVM) is None

    @pytest.mark.django_db
    def test_resolve_account_logs_into_the_owning_account(self):
        # Logging in with a secondary signs into the account that owns it.
        owner = link("owner", ALGO, is_primary=True, login_enabled=True)
        LinkedAddress.objects.create(
            profile=owner.profile,
            address=EVM,
            canonical_address=EVM,
            chain="evm",
            auth_method="evm_xchain",
            is_primary=False,
            login_enabled=True,
        )
        assert resolve_account("evm", EVM) == owner
