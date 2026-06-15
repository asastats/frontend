"""Testing module for :py:mod:`walletauth.gating` module."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from walletauth.gating import is_linked_to_user, linked_addresses_for_user
from walletauth.models import LinkedAddress

user_model = get_user_model()

ALGO = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
EVM = "0x52908400098527886e0f7030069857d2e4169ee7"
LSIG = "LSIGCOUNTERPART57NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63"


def make_user(username="owner"):
    return user_model.objects.create(username=username)


def link(profile, address, canonical, *, login=True, primary=True):
    return LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=canonical,
        chain="evm" if address.startswith("0x") else "algorand",
        auth_method="evm_xchain" if address.startswith("0x") else "algorand_wallet",
        is_primary=primary,
        login_enabled=login,
    )


class TestIsLinkedToUser:
    """Testing class for :func:`is_linked_to_user`."""

    @pytest.mark.django_db
    def test_true_for_connected_algorand_address(self):
        user = make_user()
        link(user.profile, ALGO, ALGO)
        assert is_linked_to_user(user, ALGO) is True

    @pytest.mark.django_db
    def test_false_for_unconnected_address(self):
        user = make_user()
        link(user.profile, ALGO, ALGO)
        assert is_linked_to_user(user, "SOMEOTHERADDRESS") is False

    @pytest.mark.django_db
    def test_evm_connection_matches_either_form(self):
        # Connected as an EVM wallet: browsing the 0x form OR its lsig matches.
        user = make_user()
        link(user.profile, EVM, LSIG, primary=False, login=False)
        assert is_linked_to_user(user, EVM) is True
        assert is_linked_to_user(user, LSIG) is True
        assert is_linked_to_user(user, EVM.upper()) is True  # case-folded

    @pytest.mark.django_db
    def test_secondary_gates_regardless_of_login_enabled(self):
        # The gate is about connection, not login: an opted-out secondary counts.
        user = make_user()
        link(user.profile, ALGO, ALGO)  # primary
        link(user.profile, EVM, LSIG, primary=False, login=False)
        assert is_linked_to_user(user, EVM) is True

    @pytest.mark.django_db
    def test_self_scoped_does_not_leak_other_accounts(self):
        owner = make_user("owner")
        link(owner.profile, ALGO, ALGO)
        other = make_user("other")
        link(other.profile, "OTHERPRIMARYADDR", "OTHERPRIMARYADDR")
        # `other` browsing owner's address must not match.
        assert is_linked_to_user(other, ALGO) is False

    @pytest.mark.django_db
    def test_anonymous_user_is_never_linked(self):
        assert is_linked_to_user(AnonymousUser(), ALGO) is False

    @pytest.mark.django_db
    def test_empty_address_is_false(self):
        user = make_user()
        link(user.profile, ALGO, ALGO)
        assert is_linked_to_user(user, "") is False


class TestLinkedAddressesForUser:
    """Testing class for :func:`linked_addresses_for_user`."""

    @pytest.mark.django_db
    def test_returns_connected_subset_in_one_pass(self):
        user = make_user()
        link(user.profile, ALGO, ALGO)
        link(user.profile, EVM, LSIG, primary=False, login=False)
        result = linked_addresses_for_user(user, [ALGO, "UNCONNECTED", EVM, LSIG])
        assert result == {ALGO, EVM, LSIG}

    @pytest.mark.django_db
    def test_empty_input_returns_empty(self):
        user = make_user()
        link(user.profile, ALGO, ALGO)
        assert linked_addresses_for_user(user, []) == set()
        assert linked_addresses_for_user(user, [None, ""]) == set()

    @pytest.mark.django_db
    def test_anonymous_returns_empty(self):
        assert linked_addresses_for_user(AnonymousUser(), [ALGO]) == set()
