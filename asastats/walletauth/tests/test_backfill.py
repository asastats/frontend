"""Testing module for the primary-LinkedAddress backfill data migration."""

import importlib

import pytest
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model

from walletauth.models import LinkedAddress

user_model = get_user_model()

backfill = importlib.import_module(
    "walletauth.migrations.0004_backfill_primary_linked_addresses"
)


def make_profile(username, address, *, authorized="", auth_method=""):
    user = user_model.objects.create(username=username)
    profile = user.profile
    profile.address = address
    profile.authorized = authorized
    profile.auth_method = auth_method
    profile.save()
    return profile


class TestBackfillPrimaryLinkedAddresses:
    """Testing class for the ``forwards``/``backwards`` backfill operations."""

    # # forwards
    @pytest.mark.django_db
    def test_forwards_mirrors_native_primary(self):
        profile = make_profile(
            "nat", "ALGOADDR1", authorized="tx1", auth_method="algorand_wallet"
        )
        backfill.forwards(django_apps, None)
        row = LinkedAddress.objects.get(profile=profile)
        assert row.is_primary is True
        assert row.login_enabled is True
        assert row.canonical_address == "ALGOADDR1"
        assert row.chain == "algorand"
        assert row.auth_method == "algorand_wallet"
        assert row.authorized == "tx1"

    @pytest.mark.django_db
    def test_forwards_canonicalizes_evm_primary(self, mocker):
        mocker.patch("utils.clients.algod_instance", return_value=object())
        mocker.patch("nameservice.xchain.check_evm_address", return_value="LSIGADDR")
        profile = make_profile("evm", "0xabc", authorized="tx2")
        backfill.forwards(django_apps, None)
        row = LinkedAddress.objects.get(profile=profile)
        assert row.canonical_address == "LSIGADDR"
        assert row.chain == "evm"
        assert row.auth_method == "evm_xchain"

    @pytest.mark.django_db
    def test_forwards_raises_when_evm_primary_uncanonicalizable(self, mocker):
        # algod unreachable: check_evm_address returns its input unchanged.
        mocker.patch("utils.clients.algod_instance", return_value=object())
        mocker.patch("nameservice.xchain.check_evm_address", side_effect=lambda a, c: a)
        make_profile("evmbad", "0xabc", authorized="tx")
        with pytest.raises(RuntimeError):
            backfill.forwards(django_apps, None)

    @pytest.mark.django_db
    def test_forwards_skips_profiles_without_address(self):
        profile = make_profile("empty", "")
        backfill.forwards(django_apps, None)
        assert not LinkedAddress.objects.filter(profile=profile).exists()

    @pytest.mark.django_db
    def test_forwards_is_idempotent(self):
        make_profile("nat", "ALGOADDR1", authorized="tx1")
        backfill.forwards(django_apps, None)
        backfill.forwards(django_apps, None)
        assert LinkedAddress.objects.filter(canonical_address="ALGOADDR1").count() == 1

    # # backwards
    @pytest.mark.django_db
    def test_backwards_removes_primary_rows(self):
        make_profile("nat", "ALGOADDR1", authorized="tx1")
        backfill.forwards(django_apps, None)
        backfill.backwards(django_apps, None)
        assert not LinkedAddress.objects.filter(is_primary=True).exists()
