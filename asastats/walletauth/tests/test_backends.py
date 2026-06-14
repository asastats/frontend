"""Testing module for :py:mod:`walletauth.backends` module."""

import pytest
from django.contrib.auth import authenticate, get_user_model

from walletauth.account_resolution import AmbiguousWalletAddress
from walletauth.backends import WalletAddressBackend

user_model = get_user_model()

LINKED_ADDRESS = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


def make_linked_user(username="backenduser", address=LINKED_ADDRESS):
    user = user_model.objects.create(username=username)
    user.profile.address = address
    user.profile.authorized = "proof"
    user.profile.save()
    return user


class TestWalletAddressBackend:
    """Testing class for :class:`WalletAddressBackend`."""

    # # authenticate
    @pytest.mark.django_db
    def test_backend_authenticate_returns_linked_user(self):
        user = make_linked_user()
        backend = WalletAddressBackend()
        assert (
            backend.authenticate(None, verified_wallet_address=LINKED_ADDRESS) == user
        )

    @pytest.mark.django_db
    def test_backend_authenticate_none_without_address(self):
        backend = WalletAddressBackend()
        assert backend.authenticate(None) is None

    @pytest.mark.django_db
    def test_backend_authenticate_ignores_password_credentials(self):
        # Reachability check: username/password must never resolve a user here.
        backend = WalletAddressBackend()
        assert backend.authenticate(None, username="x", password="y") is None

    @pytest.mark.django_db
    def test_backend_resolves_through_django_authenticate(self):
        user = make_linked_user("viadjango")
        resolved = authenticate(None, verified_wallet_address=LINKED_ADDRESS)
        assert resolved == user
        assert resolved.backend.endswith("WalletAddressBackend")

    @pytest.mark.django_db
    def test_backend_authenticate_propagates_ambiguity(self):
        make_linked_user("dup_a")
        make_linked_user("dup_b")  # same address, second account
        backend = WalletAddressBackend()
        with pytest.raises(AmbiguousWalletAddress):
            backend.authenticate(None, verified_wallet_address=LINKED_ADDRESS)

    # # get_user
    @pytest.mark.django_db
    def test_backend_get_user_returns_user(self):
        user = make_linked_user("getuser")
        assert WalletAddressBackend().get_user(user.pk) == user

    @pytest.mark.django_db
    def test_backend_get_user_none_for_missing(self):
        assert WalletAddressBackend().get_user(999999) is None
