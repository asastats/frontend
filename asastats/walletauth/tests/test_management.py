"""Testing module for :py:mod:`walletauth.management` module."""

import pytest
from django.contrib.auth import get_user_model

from walletauth.management import (
    CannotDisablePrimaryLogin,
    CannotRemovePrimary,
    remove_address,
    set_login_enabled,
    set_primary,
)
from walletauth.models import LinkedAddress

user_model = get_user_model()

ALGO_A = "AAAA4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
ALGO_B = "BBBB4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


@pytest.fixture(autouse=True)
def _stub_permission_refresh(mocker):
    # Keep update_authorized's permission re-derivation deterministic/offline.
    mocker.patch("core.models.Profile.check_votes_and_permission")


def make_user(username="owner"):
    return user_model.objects.create(username=username)


def primary(profile, address=ALGO_A, authorized="p"):
    profile.address = address
    profile.authorized = authorized
    profile.save()
    return LinkedAddress.objects.create(
        profile=profile, address=address, canonical_address=address,
        chain="algorand", auth_method="algorand_wallet",
        authorized=authorized, is_primary=True, login_enabled=True,
    )


def secondary(profile, address=ALGO_B, *, login=False, authorized="s"):
    return LinkedAddress.objects.create(
        profile=profile, address=address, canonical_address=address,
        chain="algorand", auth_method="algorand_wallet",
        authorized=authorized, is_primary=False, login_enabled=login,
    )


class TestSetPrimary:
    """Testing class for :func:`set_primary`."""

    @pytest.mark.django_db
    def test_set_primary_promotes_and_demotes(self):
        user = make_user()
        old = primary(user.profile)
        new = secondary(user.profile)
        set_primary(user.profile, new)
        old.refresh_from_db()
        new.refresh_from_db()
        assert new.is_primary is True
        assert new.login_enabled is True
        assert old.is_primary is False
        assert LinkedAddress.objects.filter(
            profile=user.profile, is_primary=True
        ).count() == 1

    @pytest.mark.django_db
    def test_set_primary_mirrors_to_profile_and_reauthorizes(self):
        user = make_user()
        primary(user.profile, address=ALGO_A, authorized="old")
        new = secondary(user.profile, address=ALGO_B, authorized="newproof")
        set_primary(user.profile, new)
        user.profile.refresh_from_db()
        assert user.profile.address == ALGO_B
        assert user.profile.authorized == "newproof"
        assert user.profile.auth_method == "algorand_wallet"

    @pytest.mark.django_db
    def test_set_primary_noop_when_already_primary(self):
        user = make_user()
        old = primary(user.profile)
        assert set_primary(user.profile, old) is True
        old.refresh_from_db()
        assert old.is_primary is True

    @pytest.mark.django_db
    def test_set_primary_reports_permission_pending(self, mocker):
        mocker.patch(
            "core.models.Profile.update_authorized", return_value=False
        )
        user = make_user()
        primary(user.profile)
        new = secondary(user.profile)
        assert set_primary(user.profile, new) is False


class TestRemoveAddress:
    """Testing class for :func:`remove_address`."""

    @pytest.mark.django_db
    def test_remove_secondary(self):
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile)
        remove_address(user.profile, sec)
        assert not LinkedAddress.objects.filter(pk=sec.pk).exists()

    @pytest.mark.django_db
    def test_remove_primary_is_rejected(self):
        user = make_user()
        prim = primary(user.profile)
        with pytest.raises(CannotRemovePrimary):
            remove_address(user.profile, prim)
        assert LinkedAddress.objects.filter(pk=prim.pk).exists()


class TestSetLoginEnabled:
    """Testing class for :func:`set_login_enabled`."""

    @pytest.mark.django_db
    def test_enable_secondary_login(self):
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile, login=False)
        set_login_enabled(user.profile, sec, True)
        sec.refresh_from_db()
        assert sec.login_enabled is True

    @pytest.mark.django_db
    def test_disable_secondary_login(self):
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile, login=True)
        set_login_enabled(user.profile, sec, False)
        sec.refresh_from_db()
        assert sec.login_enabled is False

    @pytest.mark.django_db
    def test_cannot_disable_primary_login(self):
        user = make_user()
        prim = primary(user.profile)
        with pytest.raises(CannotDisablePrimaryLogin):
            set_login_enabled(user.profile, prim, False)
