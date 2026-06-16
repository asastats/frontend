"""Testing module for :py:mod:`walletauth.linking` module."""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from walletauth.linking import (
    AddressAlreadyLinked,
    SecondaryLimitReached,
    link_address,
    sync_primary_linked,
)
from walletauth.models import LinkedAddress

user_model = get_user_model()

ALGO_A = "AAAA4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
ALGO_B = "BBBB4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
ALGO_C = "CCCC4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


def make_user(username="owner"):
    return user_model.objects.create(username=username)


@pytest.fixture(autouse=True)
def _stub_permission_refresh(mocker):
    # Against the real core.Profile, update_authorized -> check_votes_and_permission
    # reaches the permission provider, which is unavailable in CI and would make
    # the best-effort refresh report permission_pending=True. Stub it so the
    # primary-bootstrap outcome is deterministic and network-free.
    mocker.patch("core.models.Profile.check_votes_and_permission")


class TestLinkAddress:
    """Testing class for :func:`link_address`."""

    # # primary bootstrap
    @pytest.mark.django_db
    def test_first_address_bootstraps_primary(self):
        user = make_user()
        result = link_address(
            user.profile,
            chain="algorand",
            address=ALGO_A,
            auth_method="algorand_wallet",
            authorized="tx1",
        )
        assert result.is_primary is True
        assert result.permission_pending is False
        user.profile.refresh_from_db()
        assert user.profile.address == ALGO_A
        assert user.profile.authorized == "tx1"
        row = LinkedAddress.objects.get(profile=user.profile)
        assert row.is_primary is True
        assert row.login_enabled is True
        assert row.canonical_address == ALGO_A

    # # secondary
    @pytest.mark.django_db
    def test_second_address_is_secondary_and_does_not_touch_primary(self):
        user = make_user()
        link_address(
            user.profile, chain="algorand", address=ALGO_A,
            auth_method="algorand_wallet", authorized="tx1",
        )
        result = link_address(
            user.profile, chain="algorand", address=ALGO_B,
            auth_method="algorand_wallet", authorized="tx2",
        )
        assert result.is_primary is False
        assert result.permission_pending is False
        user.profile.refresh_from_db()
        # Primary untouched: permission/identity stay on the first address.
        assert user.profile.address == ALGO_A
        assert user.profile.authorized == "tx1"
        secondary = LinkedAddress.objects.get(canonical_address=ALGO_B)
        assert secondary.is_primary is False
        assert secondary.login_enabled is False

    @pytest.mark.django_db
    def test_has_primary_recognized_from_registry_row_alone(self):
        # No Profile.address, but a primary row exists -> next link is secondary.
        user = make_user()
        LinkedAddress.objects.create(
            profile=user.profile, address=ALGO_A, canonical_address=ALGO_A,
            chain="algorand", auth_method="algorand_wallet",
            is_primary=True, login_enabled=True,
        )
        result = link_address(
            user.profile, chain="algorand", address=ALGO_B,
            auth_method="algorand_wallet", authorized="tx2",
        )
        assert result.is_primary is False

    # # idempotent re-link
    @pytest.mark.django_db
    def test_relinking_own_address_is_idempotent(self):
        user = make_user()
        link_address(
            user.profile, chain="algorand", address=ALGO_A,
            auth_method="algorand_wallet", authorized="tx1",
        )
        result = link_address(
            user.profile, chain="algorand", address=ALGO_A,
            auth_method="algorand_wallet", authorized="tx1-again",
        )
        assert result.is_primary is True
        assert LinkedAddress.objects.filter(canonical_address=ALGO_A).count() == 1
        assert LinkedAddress.objects.get(canonical_address=ALGO_A).authorized == "tx1-again"

    # # collision
    @pytest.mark.django_db
    def test_address_linked_to_another_account_is_rejected(self):
        other = make_user("other")
        link_address(
            other.profile, chain="algorand", address=ALGO_A,
            auth_method="algorand_wallet", authorized="tx1",
        )
        user = make_user("me")
        link_address(
            user.profile, chain="algorand", address=ALGO_B,
            auth_method="algorand_wallet", authorized="txb",
        )
        with pytest.raises(AddressAlreadyLinked):
            link_address(
                user.profile, chain="algorand", address=ALGO_A,
                auth_method="algorand_wallet", authorized="txx",
            )

    # # capacity
    @pytest.mark.django_db
    def test_secondary_cap_is_enforced(self):
        user = make_user()
        link_address(
            user.profile, chain="algorand", address=ALGO_A,
            auth_method="algorand_wallet", authorized="tx1",
        )
        with override_settings(MAX_SECONDARY_ADDRESSES=1):
            link_address(
                user.profile, chain="algorand", address=ALGO_B,
                auth_method="algorand_wallet", authorized="tx2",
            )
            with pytest.raises(SecondaryLimitReached):
                link_address(
                    user.profile, chain="algorand", address=ALGO_C,
                    auth_method="algorand_wallet", authorized="tx3",
                )

    # # evm canonicalization
    @pytest.mark.django_db
    def test_evm_secondary_stores_lsig_canonical(self, mocker):
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        mocker.patch(
            "walletauth.addresses.check_evm_address",
            side_effect=lambda a, c: "LSIG" + a[2:].upper(),
        )
        user = make_user()
        link_address(
            user.profile, chain="algorand", address=ALGO_A,
            auth_method="algorand_wallet", authorized="tx1",
        )
        evm = "0x52908400098527886e0f7030069857d2e4169ee7"
        result = link_address(
            user.profile, chain="evm", address=evm,
            auth_method="evm_xchain", authorized="txe",
        )
        assert result.is_primary is False
        row = LinkedAddress.objects.get(address=evm)
        assert row.canonical_address == "LSIG" + evm[2:].upper()
        assert row.chain == "evm"


class TestSyncPrimaryLinked:
    """Testing class for :func:`sync_primary_linked`."""

    @pytest.mark.django_db
    def test_no_address_is_noop(self):
        user = make_user()
        assert sync_primary_linked(user.profile) is None
        assert not LinkedAddress.objects.filter(profile=user.profile).exists()

    @pytest.mark.django_db
    def test_creates_primary_row_for_authorized_address(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.authorized = "tx1"
        user.profile.auth_method = "algorand_wallet"
        user.profile.save()
        row = sync_primary_linked(user.profile)
        assert row.is_primary is True
        assert row.login_enabled is True
        assert row.canonical_address == ALGO_A
        assert row.authorized == "tx1"

    @pytest.mark.django_db
    def test_refreshes_existing_primary_row(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.authorized = "tx1"
        user.profile.save()
        first = sync_primary_linked(user.profile)
        user.profile.authorized = "tx2"
        user.profile.save()
        second = sync_primary_linked(user.profile)
        assert second.pk == first.pk
        assert second.authorized == "tx2"

    @pytest.mark.django_db
    def test_replaces_stale_primary_when_address_changes(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.authorized = "tx1"
        user.profile.save()
        sync_primary_linked(user.profile)
        # User changed their primary address and re-authorized.
        user.profile.address = ALGO_B
        user.profile.authorized = "tx2"
        user.profile.save()
        row = sync_primary_linked(user.profile)
        assert row.canonical_address == ALGO_B
        assert not LinkedAddress.objects.filter(canonical_address=ALGO_A).exists()
        assert LinkedAddress.objects.filter(profile=user.profile, is_primary=True).count() == 1

    @pytest.mark.django_db
    def test_promotes_existing_secondary_to_primary(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.authorized = "tx1"
        user.profile.save()
        sync_primary_linked(user.profile)
        secondary = link_address(
            user.profile, chain="algorand", address=ALGO_B,
            auth_method="algorand_wallet", authorized="tx2",
        ).linked_address
        # Now the user makes ALGO_B their primary.
        user.profile.address = ALGO_B
        user.profile.authorized = "tx2b"
        user.profile.save()
        row = sync_primary_linked(user.profile)
        assert row.pk == secondary.pk
        assert row.is_primary is True
        assert LinkedAddress.objects.filter(profile=user.profile, is_primary=True).count() == 1

    @pytest.mark.django_db
    def test_address_held_by_another_account_is_rejected(self):
        other = make_user("other")
        other.profile.address = ALGO_A
        other.profile.authorized = "tx1"
        other.profile.save()
        sync_primary_linked(other.profile)
        user = make_user("me")
        user.profile.address = ALGO_A
        user.profile.authorized = "tx2"
        user.profile.save()
        with pytest.raises(AddressAlreadyLinked):
            sync_primary_linked(user.profile)
