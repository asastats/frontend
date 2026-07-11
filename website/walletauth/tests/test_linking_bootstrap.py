"""Tests for the legacy-address link-time primary bootstrap (heal stranded rows)."""

import pytest
from django.contrib.auth import get_user_model

from walletauth.linking import link_address
from walletauth.models import LinkedAddress

user_model = get_user_model()

ALGO_A = "AAAA4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
ALGO_B = "BBBB4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


@pytest.fixture(autouse=True)
def _stub_permission(mocker):
    mocker.patch("core.models.Profile.check_votes_and_permission")


def make_user(username="owner"):
    return user_model.objects.create(username=username)


def _link(profile, address=ALGO_A):
    return link_address(
        profile,
        chain="algorand",
        address=address,
        auth_method="algorand_wallet",
        authorized="tx",
    )


class TestLegacyProfileAddressBootstrap:
    @pytest.mark.django_db
    def test_linking_the_legacy_profile_address_becomes_primary(self):
        # profile.address preset (legacy), no primary LinkedAddress yet.
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.save()
        result = _link(user.profile, ALGO_A)
        assert result.is_primary is True
        row = LinkedAddress.objects.get(profile=user.profile, address=ALGO_A)
        assert row.is_primary is True
        assert row.login_enabled is True

    @pytest.mark.django_db
    def test_linking_a_different_address_stays_secondary(self):
        # Legacy address is A; linking B is a real primary change -> secondary.
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.save()
        result = _link(user.profile, ALGO_B)
        assert result.is_primary is False

    @pytest.mark.django_db
    def test_relinking_a_stranded_row_heals_to_primary(self):
        # Simulate the pre-fix stranded state: profile.address set, a non-primary
        # LinkedAddress for it, and no primary at all.
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.save()
        LinkedAddress.objects.create(
            profile=user.profile,
            address=ALGO_A,
            canonical_address=ALGO_A,
            chain="algorand",
            auth_method="algorand_wallet",
            authorized="old",
            is_primary=False,
            login_enabled=False,
        )
        result = _link(user.profile, ALGO_A)  # re-link the same address
        assert result.is_primary is True
        row = LinkedAddress.objects.get(profile=user.profile, address=ALGO_A)
        assert row.is_primary is True
        assert row.login_enabled is True

    @pytest.mark.django_db
    def test_relink_does_not_promote_when_a_primary_exists(self):
        # A different primary exists; re-linking a secondary must not steal it.
        user = make_user()
        user.profile.address = ALGO_B
        user.profile.save()
        LinkedAddress.objects.create(
            profile=user.profile,
            address=ALGO_B,
            canonical_address=ALGO_B,
            chain="algorand",
            auth_method="algorand_wallet",
            authorized="p",
            is_primary=True,
            login_enabled=True,
        )
        LinkedAddress.objects.create(
            profile=user.profile,
            address=ALGO_A,
            canonical_address=ALGO_A,
            chain="algorand",
            auth_method="algorand_wallet",
            authorized="s",
            is_primary=False,
            login_enabled=False,
        )
        result = _link(user.profile, ALGO_A)
        assert result.is_primary is False
