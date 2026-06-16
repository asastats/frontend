"""Testing module for :py:mod:`walletauth.views` module."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.models import LinkedAddress, WalletNonce
from walletauth.throttling import WalletAuthRateThrottle
from walletauth.verifiers import NotSupported
from walletauth.views import (
    WalletNonceAPIView,
    WalletsAPIView,
    WalletVerifyAPIView,
)

user_model = get_user_model()

TEST_ADDRESS = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
OTHER_ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"


# # HELPERS
def make_authorized_user(address=TEST_ADDRESS):
    user = user_model.objects.create(username="walletuser")
    user.profile.address = address
    user.profile.save()
    return user


class _FakeVerifier:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def verify(self, *, address, nonce, prefix, payload):
        if self.error is not None:
            raise self.error
        return self.result


class TestWalletsAPIView:
    """Testing class for :class:`WalletsAPIView` view."""

    # # get
    def test_walletauth_walletsapiview_is_apiview_subclass(self):
        assert issubclass(WalletsAPIView, APIView)

    def test_walletauth_walletsapiview_get_returns_wallets(self):
        request = APIRequestFactory().get("/wallets/")
        response = WalletsAPIView.as_view()(request)
        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert {"id", "name"}.issubset(response.data[0].keys())


class TestWalletNonceAPIView:
    """Testing class for :class:`WalletNonceAPIView` view."""

    # # configuration
    def test_walletauth_nonceview_uses_walletauth_throttle(self):
        assert WalletAuthRateThrottle in WalletNonceAPIView.throttle_classes

    # # post
    @pytest.mark.django_db
    def test_walletauth_nonceview_creates_nonce_for_own_address(self):
        user = make_authorized_user()
        request = APIRequestFactory().post(
            "/nonce/", {"address": TEST_ADDRESS}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletNonceAPIView.as_view()(request)

        assert response.status_code == 200
        assert response.data["prefix"] == WALLET_CONNECT_NONCE_PREFIX
        nonce = WalletNonce.objects.get(nonce=response.data["nonce"])
        assert nonce.user == user
        assert nonce.address == TEST_ADDRESS

    @pytest.mark.django_db
    def test_walletauth_nonceview_rejects_address_mismatch(self):
        user = make_authorized_user()
        request = APIRequestFactory().post(
            "/nonce/", {"address": OTHER_ADDRESS}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletNonceAPIView.as_view()(request)
        assert response.status_code == 400
        assert WalletNonce.objects.count() == 0

    @pytest.mark.django_db
    def test_walletauth_nonceview_rejects_invalid_address(self):
        user = make_authorized_user()
        request = APIRequestFactory().post(
            "/nonce/", {"address": "not-an-address"}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletNonceAPIView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_walletauth_nonceview_rejects_unsupported_chain(self):
        user = make_authorized_user()
        request = APIRequestFactory().post(
            "/nonce/", {"address": TEST_ADDRESS, "chain": "solana"}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletNonceAPIView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_walletauth_nonceview_requires_authentication(self):
        request = APIRequestFactory().post(
            "/nonce/", {"address": TEST_ADDRESS}, format="json"
        )
        response = WalletNonceAPIView.as_view()(request)
        assert response.status_code in (401, 403)


class TestWalletVerifyAPIView:
    """Testing class for :class:`WalletVerifyAPIView` view."""

    # # configuration
    def test_walletauth_verifyview_uses_walletauth_throttle(self):
        assert WalletAuthRateThrottle in WalletVerifyAPIView.throttle_classes

    # # HELPERS
    @staticmethod
    def post(user, data, mocker, verifier=None):
        if verifier is not None:
            mocker.patch.dict("walletauth.views.VERIFIERS", {"algorand": verifier})
        mocker.patch("core.models.Profile.check_votes_and_permission")
        request = APIRequestFactory().post("/verify/", data, format="json")
        force_authenticate(request, user=user)
        return WalletVerifyAPIView.as_view()(request)

    # # post
    @pytest.mark.django_db
    def test_walletauth_verifyview_authorizes_on_success(self, mocker):
        user = make_authorized_user()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        response = self.post(
            user,
            {"nonce": "good", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(result=TEST_ADDRESS),
        )

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["permission_pending"] is False
        user.profile.refresh_from_db()
        assert user.profile.authorized == "good"
        assert user.profile.auth_method == "algorand_wallet"
        assert WalletNonce.objects.get(nonce="good").used is True

    @pytest.mark.django_db
    def test_walletauth_verifyview_mirrors_primary_into_registry(self, mocker):
        user = make_authorized_user()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        self.post(
            user,
            {"nonce": "good", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(result=TEST_ADDRESS),
        )
        row = LinkedAddress.objects.get(profile=user.profile, is_primary=True)
        assert row.canonical_address == TEST_ADDRESS
        assert row.login_enabled is True
        assert row.authorized == "good"

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_address_held_by_another_account(
        self, mocker
    ):
        # Another account already owns this canonical address in the registry.
        other = user_model.objects.create(username="holder")
        LinkedAddress.objects.create(
            profile=other.profile,
            address=TEST_ADDRESS,
            canonical_address=TEST_ADDRESS,
            chain="algorand",
            auth_method="algorand_wallet",
            is_primary=True,
            login_enabled=True,
        )
        user = user_model.objects.create(username="claimer")
        user.profile.address = TEST_ADDRESS
        user.profile.save()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        response = self.post(
            user,
            {"nonce": "good", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(result=TEST_ADDRESS),
        )
        assert response.status_code == 409
        # The authorization was rolled back, not half-applied.
        user.profile.refresh_from_db()
        assert user.profile.authorized != "good"

    @pytest.mark.django_db
    def test_walletauth_verifyview_authorizes_when_permission_refresh_fails(
        self, mocker
    ):
        user = make_authorized_user()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        mocker.patch.dict(
            "walletauth.views.VERIFIERS",
            {"algorand": _FakeVerifier(result=TEST_ADDRESS)},
        )
        mocker.patch(
            "core.models.Profile.check_votes_and_permission",
            side_effect=RuntimeError("algod unreachable"),
        )
        request = APIRequestFactory().post(
            "/verify/", {"nonce": "good", "chain": "algorand"}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletVerifyAPIView.as_view()(request)

        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["permission_pending"] is True
        user.profile.refresh_from_db()
        assert user.profile.authorized == "good"
        assert user.profile.auth_method == "algorand_wallet"
        assert WalletNonce.objects.get(nonce="good").used is True

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_missing_nonce(self, mocker):
        user = make_authorized_user()
        mocker.patch("core.models.Profile.check_votes_and_permission")
        request = APIRequestFactory().post(
            "/verify/", {"chain": "algorand"}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert response.data["error"] == "Missing nonce"

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_lost_nonce_race(self, mocker):
        user = make_authorized_user()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        mocker.patch.dict(
            "walletauth.views.VERIFIERS",
            {"algorand": _FakeVerifier(result=TEST_ADDRESS)},
        )
        mocker.patch("core.models.Profile.check_votes_and_permission")
        # Simulate a concurrent request having already consumed the nonce: the
        # atomic claim loses the race and returns False.
        mocker.patch("walletauth.models.WalletNonce.claim", return_value=False)
        update = mocker.patch("core.models.Profile.update_authorized")
        request = APIRequestFactory().post(
            "/verify/", {"nonce": "good", "chain": "algorand"}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletVerifyAPIView.as_view()(request)

        assert response.status_code == 400
        assert response.data["error"] == "Nonce already used"
        update.assert_not_called()

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_unknown_nonce(self, mocker):
        user = make_authorized_user()
        response = self.post(
            user,
            {"nonce": "missing", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(result=TEST_ADDRESS),
        )
        assert response.status_code == 400
        assert response.data["success"] is False

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_expired_nonce(self, mocker):
        from datetime import timedelta

        from django.utils import timezone

        user = make_authorized_user()
        nonce = WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="old")
        WalletNonce.objects.filter(pk=nonce.pk).update(
            created_at=timezone.now() - timedelta(minutes=10)
        )
        response = self.post(
            user,
            {"nonce": "old", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(result=TEST_ADDRESS),
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_failed_proof(self, mocker):
        user = make_authorized_user()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        response = self.post(
            user,
            {"nonce": "good", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(result=None),
        )
        assert response.status_code == 400
        assert WalletNonce.objects.get(nonce="good").used is False

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_unsupported_chain(self, mocker):
        user = make_authorized_user()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        mocker.patch("core.models.Profile.check_votes_and_permission")
        request = APIRequestFactory().post(
            "/verify/", {"nonce": "good", "chain": "solana"}, format="json"
        )
        force_authenticate(request, user=user)
        response = WalletVerifyAPIView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_walletauth_verifyview_handles_not_supported(self, mocker):
        user = make_authorized_user()
        WalletNonce.objects.create(user=user, address=TEST_ADDRESS, nonce="good")
        response = self.post(
            user,
            {"nonce": "good", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(error=NotSupported("nope")),
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_walletauth_verifyview_rejects_profile_without_address(self, mocker):
        user = user_model.objects.create(username="noaddr")
        response = self.post(
            user,
            {"nonce": "good", "chain": "algorand"},
            mocker,
            verifier=_FakeVerifier(result=TEST_ADDRESS),
        )
        assert response.status_code == 400
