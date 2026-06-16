"""Testing module for :py:mod:`walletauth.models` module."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import models
from django.db.utils import IntegrityError
from django.utils import timezone

from walletauth.models import WalletLoginNonce, WalletNonce

user_model = get_user_model()

TEST_ADDRESS = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


# # HELPERS
def make_user(username="walletuser"):
    return user_model.objects.create(username=username)


def make_nonce(user=None, address=TEST_ADDRESS, nonce="abc123", **kwargs):
    return WalletNonce.objects.create(
        user=user or make_user(), address=address, nonce=nonce, **kwargs
    )


class TestWalletNonceModel:
    """Testing class for :class:`WalletNonce` model."""

    # # fields characteristics
    @pytest.mark.parametrize(
        "name,typ",
        [
            ("user", models.ForeignKey),
            ("address", models.CharField),
            ("nonce", models.CharField),
            ("chain", models.CharField),
            ("created_at", models.DateTimeField),
            ("used", models.BooleanField),
        ],
    )
    def test_walletnonce_model_fields(self, name, typ):
        assert hasattr(WalletNonce, name)
        assert isinstance(WalletNonce._meta.get_field(name), typ)

    def test_walletnonce_model_address_has_db_index(self):
        assert WalletNonce._meta.get_field("address").db_index is True

    def test_walletnonce_model_nonce_is_unique(self):
        assert WalletNonce._meta.get_field("nonce").unique is True

    def test_walletnonce_model_chain_defaults_to_algorand(self):
        assert WalletNonce._meta.get_field("chain").default == "algorand"

    # # creation
    @pytest.mark.django_db
    def test_walletnonce_model_creation_sets_defaults(self):
        nonce = make_nonce()
        assert nonce.used is False
        assert nonce.chain == "algorand"
        assert nonce.created_at is not None

    @pytest.mark.django_db
    def test_walletnonce_model_is_bound_to_user(self):
        user = make_user()
        nonce = make_nonce(user=user)
        assert nonce.user == user
        assert list(user.wallet_nonces.all()) == [nonce]

    @pytest.mark.django_db
    def test_walletnonce_model_nonce_unique_constraint(self):
        make_nonce(nonce="dup")
        with pytest.raises(IntegrityError):
            make_nonce(nonce="dup")

    @pytest.mark.django_db
    def test_walletnonce_model_deleted_with_user(self):
        user = make_user()
        make_nonce(user=user)
        user.delete()
        assert WalletNonce.objects.count() == 0

    # # __str__
    @pytest.mark.django_db
    def test_walletnonce_model_string_representation(self):
        nonce = make_nonce(nonce="xyz")
        assert str(nonce) == f"{TEST_ADDRESS[:5]}..{TEST_ADDRESS[-5:]} - xyz"

    # # is_expired
    @pytest.mark.django_db
    def test_walletnonce_model_is_expired_false_when_fresh(self):
        assert make_nonce().is_expired() is False

    @pytest.mark.django_db
    def test_walletnonce_model_is_expired_true_after_ttl(self):
        nonce = make_nonce()
        nonce.created_at = timezone.now() - timedelta(minutes=6)
        assert nonce.is_expired() is True

    @pytest.mark.django_db
    def test_walletnonce_model_is_expired_true_at_exactly_ttl(self):
        nonce = make_nonce()
        nonce.created_at = timezone.now() - WalletNonce.NONCE_TTL
        assert nonce.is_expired() is True

    # # mark_used
    @pytest.mark.django_db
    def test_walletnonce_model_mark_used_sets_flag(self):
        nonce = make_nonce()
        nonce.mark_used()
        nonce.refresh_from_db()
        assert nonce.used is True

    # # claim
    @pytest.mark.django_db
    def test_walletnonce_model_claim_consumes_once(self):
        nonce = make_nonce()
        assert nonce.claim() is True
        nonce.refresh_from_db()
        assert nonce.used is True

    @pytest.mark.django_db
    def test_walletnonce_model_claim_is_single_use(self):
        nonce = make_nonce()
        first = nonce.claim()
        # a second instance pointing at the same row must lose the race
        other = WalletNonce.objects.get(pk=nonce.pk)
        second = other.claim()
        assert first is True
        assert second is False

    @pytest.mark.django_db
    def test_walletnonce_model_claim_false_when_already_used(self):
        nonce = make_nonce(used=True)
        assert nonce.claim() is False

    @pytest.mark.django_db
    def test_walletnonce_model_mark_used_saves_only_used_field(self, mocker):
        nonce = make_nonce()
        mock_save = mocker.patch.object(nonce, "save")
        nonce.mark_used()
        mock_save.assert_called_once_with(update_fields=["used"])

    # # purge_stale
    @pytest.mark.django_db
    def test_walletnonce_model_purge_stale_removes_used_and_expired(self):
        user = make_user()
        make_nonce(user=user, nonce="fresh")
        make_nonce(user=user, nonce="used", used=True)
        expired = make_nonce(user=user, nonce="expired")
        WalletNonce.objects.filter(pk=expired.pk).update(
            created_at=timezone.now() - timedelta(minutes=10)
        )

        deleted = WalletNonce.purge_stale()

        assert deleted == 2
        assert list(WalletNonce.objects.values_list("nonce", flat=True)) == ["fresh"]


class TestWalletLoginNonce:
    """Testing class for :class:`WalletLoginNonce` model."""

    # # claim
    @pytest.mark.django_db
    def test_walletloginnonce_claim_is_single_use(self):
        nonce = WalletLoginNonce.objects.create(address="A" * 58, nonce="ln1")
        first = nonce.claim()
        second = WalletLoginNonce.objects.get(pk=nonce.pk).claim()
        assert first is True
        assert second is False

    # # is_expired
    @pytest.mark.django_db
    def test_walletloginnonce_is_expired(self):
        nonce = WalletLoginNonce.objects.create(address="A" * 58, nonce="ln2")
        assert nonce.is_expired() is False
        WalletLoginNonce.objects.filter(pk=nonce.pk).update(
            created_at=timezone.now() - timedelta(minutes=10)
        )
        assert WalletLoginNonce.objects.get(pk=nonce.pk).is_expired() is True

    # # purge_stale
    @pytest.mark.django_db
    def test_walletloginnonce_purge_stale_removes_used_and_expired(self):
        WalletLoginNonce.objects.create(address="A" * 58, nonce="fresh")
        WalletLoginNonce.objects.create(address="A" * 58, nonce="used", used=True)
        expired = WalletLoginNonce.objects.create(address="A" * 58, nonce="exp")
        WalletLoginNonce.objects.filter(pk=expired.pk).update(
            created_at=timezone.now() - timedelta(minutes=10)
        )

        deleted = WalletLoginNonce.purge_stale()

        assert deleted == 2
        assert list(WalletLoginNonce.objects.values_list("nonce", flat=True)) == [
            "fresh"
        ]

    # # __str__
    @pytest.mark.django_db
    def test_walletloginnonce_str(self):
        nonce = WalletLoginNonce.objects.create(address="A" * 58, nonce="lnstr")
        assert "login" in str(nonce)
