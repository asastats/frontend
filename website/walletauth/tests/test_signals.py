"""Testing module for :py:mod:`walletauth.signals` module."""

import pytest
from django.contrib.auth import get_user_model

from walletauth.models import LinkedAddress

user_model = get_user_model()

ALGO_A = "AAAA4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
ALGO_B = "BBBB4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


@pytest.fixture(autouse=True)
def _stub_permission_refresh(mocker):
    mocker.patch("core.models.Profile.check_votes_and_permission")


def make_user(name="owner"):
    return user_model.objects.create(username=name)


def primary_row(profile, address):
    return LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=address,
        chain="algorand",
        auth_method="algorand_wallet",
        is_primary=True,
        login_enabled=True,
    )


class TestReconcilePrimaryRegistry:
    """Testing class for :func:`reconcile_primary_registry`."""

    @pytest.mark.django_db
    def test_clearing_profile_address_drops_stale_primary(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.save()
        primary_row(user.profile, ALGO_A)
        user.profile.address = ""
        user.profile.save()
        assert not LinkedAddress.objects.filter(
            profile=user.profile, is_primary=True
        ).exists()

    @pytest.mark.django_db
    def test_changing_profile_address_drops_old_primary(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.save()
        primary_row(user.profile, ALGO_A)
        user.profile.address = ALGO_B
        user.profile.save()
        assert not LinkedAddress.objects.filter(
            address=ALGO_A, is_primary=True
        ).exists()

    @pytest.mark.django_db
    def test_same_address_save_keeps_primary(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.save()
        row = primary_row(user.profile, ALGO_A)
        user.profile.save()
        assert LinkedAddress.objects.filter(pk=row.pk, is_primary=True).exists()

    @pytest.mark.django_db
    def test_deleted_primary_cannot_be_used_for_login(self):
        user = make_user()
        user.profile.address = ALGO_A
        user.profile.save()
        primary_row(user.profile, ALGO_A)
        user.profile.address = ""
        user.profile.save()
        # The login-capable row is gone: a removed address can't sign in.
        assert not LinkedAddress.objects.filter(
            address=ALGO_A, login_enabled=True
        ).exists()

    @pytest.mark.django_db
    def test_reconcile_never_breaks_profile_save(self, mocker):
        user = make_user()
        mocker.patch(
            "walletauth.signals.LinkedAddress.objects.filter",
            side_effect=RuntimeError("boom"),
        )
        # A failure inside reconciliation must not propagate out of save().
        user.profile.address = ALGO_A
        user.profile.save()
