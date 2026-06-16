"""Testing module for the :class:`walletauth.models.LinkedAddress` model."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import override_settings

from walletauth.models import LinkedAddress

user_model = get_user_model()


def make_user(username="owner"):
    return user_model.objects.create(username=username)


def link(
    profile, canonical, *, address="A", chain="algorand", primary=False, login=False
):
    return LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=canonical,
        chain=chain,
        auth_method="algorand_wallet" if chain == "algorand" else "evm_xchain",
        is_primary=primary,
        login_enabled=login,
    )


class TestLinkedAddressConstraints:
    """Testing class for the database constraints on :class:`LinkedAddress`."""

    # # uniqueness
    @pytest.mark.django_db
    def test_canonical_address_is_globally_unique(self):
        link(make_user("u1").profile, "CANON", primary=True, login=True)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                link(make_user("u2").profile, "CANON")

    @pytest.mark.django_db
    def test_only_one_primary_per_profile(self):
        user = make_user()
        link(user.profile, "C1", primary=True, login=True)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                link(user.profile, "C2", primary=True, login=True)

    @pytest.mark.django_db
    def test_two_profiles_may_each_have_a_primary(self):
        link(make_user("u1").profile, "C1", primary=True, login=True)
        link(make_user("u2").profile, "C2", primary=True, login=True)
        assert LinkedAddress.objects.filter(is_primary=True).count() == 2

    # # check constraint
    @pytest.mark.django_db
    def test_primary_must_be_login_enabled(self):
        user = make_user()
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                link(user.profile, "C", primary=True, login=False)

    @pytest.mark.django_db
    def test_secondary_may_have_login_disabled(self):
        user = make_user()
        secondary = link(user.profile, "C", primary=False, login=False)
        assert secondary.pk is not None


class TestLinkedAddressHelpers:
    """Testing class for :class:`LinkedAddress` helper methods."""

    # # secondary_count
    @pytest.mark.django_db
    def test_secondary_count_excludes_primary(self):
        user = make_user()
        link(user.profile, "CP", primary=True, login=True)
        link(user.profile, "CS1", chain="evm")
        link(user.profile, "CS2", chain="evm")
        assert LinkedAddress.secondary_count(user.profile) == 2

    # # at_secondary_capacity
    @pytest.mark.django_db
    def test_at_secondary_capacity_respects_limit(self):
        user = make_user()
        with override_settings(MAX_SECONDARY_ADDRESSES=2):
            assert LinkedAddress.at_secondary_capacity(user.profile) is False
            link(user.profile, "CS1", chain="evm")
            assert LinkedAddress.at_secondary_capacity(user.profile) is False
            link(user.profile, "CS2", chain="evm")
            assert LinkedAddress.at_secondary_capacity(user.profile) is True

    # # __str__
    @pytest.mark.django_db
    def test_str_marks_primary_and_secondary(self):
        user = make_user()
        primary = link(user.profile, "CP", address="PRIM", primary=True, login=True)
        secondary = link(user.profile, "CS", address="SEC", chain="evm")
        assert "primary" in str(primary)
        assert "secondary" in str(secondary)
