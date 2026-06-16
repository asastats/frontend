"""Testing module for :py:mod:`walletauth.backends` module."""

import pytest
from django.contrib.auth import authenticate, get_user_model

from walletauth.account_resolution import AmbiguousWalletAddress
from walletauth.backends import WalletAddressBackend
from walletauth.models import LinkedAddress

user_model = get_user_model()

LINKED_ADDRESS = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


def make_linked_user(username="backenduser", address=LINKED_ADDRESS):
    user = user_model.objects.create(username=username)
    LinkedAddress.objects.create(
        profile=user.profile,
        address=address,
        canonical_address=address,
        chain="algorand",
        auth_method="algorand_wallet",
        is_primary=True,
        login_enabled=True,
    )
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
    def test_backend_authenticate_propagates_ambiguity(self, mocker):
        # The canonical unique constraint prevents two rows sharing an address,
        # so force the defensive branch to confirm the backend propagates it.
        queryset = mocker.MagicMock()
        queryset.get.side_effect = LinkedAddress.MultipleObjectsReturned
        mocker.patch.object(
            LinkedAddress.objects, "select_related", return_value=queryset
        )
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
