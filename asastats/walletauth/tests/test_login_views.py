"""Testing module for :py:mod:`walletauth.login_views` module."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.login_views import (
    WalletLoginNonceAPIView,
    WalletLoginVerifyAPIView,
)
from walletauth.models import WalletLoginNonce
from walletauth.throttling import WalletLoginRateThrottle
from walletauth.verifiers import NotSupported

user_model = get_user_model()

PROVEN = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
OTHER = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
EVM_ADDRESS = "0x52908400098527886E0F7030069857D2E4169EE7"


def link_user(address=PROVEN, username="loginuser"):
    user = user_model.objects.create(username=username)
    user.profile.address = address
    user.profile.authorized = "proof"
    user.profile.save()
    return user


class _FakeLoginVerifier:
    def __init__(self, proven=None, error=None):
        self.proven = proven
        self.error = error

    def recover(self, *, nonce, prefix, payload):
        if self.error is not None:
            raise self.error
        return self.proven


def _patch_verifier(mocker, verifier):
    mocker.patch.dict("walletauth.login_views.VERIFIERS", {"algorand": verifier})


class TestWalletLoginNonceAPIView:
    """Testing class for :class:`WalletLoginNonceAPIView`."""

    # # configuration
    def test_login_nonce_is_anonymous_and_throttled(self):
        assert WalletLoginRateThrottle in WalletLoginNonceAPIView.throttle_classes

    # # post
    @pytest.mark.django_db
    def test_login_nonce_creates_address_bound_nonce(self):
        request = APIRequestFactory().post(
            "/login/nonce/", {"address": PROVEN}, format="json"
        )
        response = WalletLoginNonceAPIView.as_view()(request)
        assert response.status_code == 200
        assert response.data["prefix"] == WALLET_CONNECT_NONCE_PREFIX
        nonce = WalletLoginNonce.objects.get(nonce=response.data["nonce"])
        assert nonce.address == PROVEN
        assert nonce.chain == "algorand"

    @pytest.mark.django_db
    def test_login_nonce_rejects_invalid_address(self):
        request = APIRequestFactory().post(
            "/login/nonce/", {"address": "not-an-address"}, format="json"
        )
        response = WalletLoginNonceAPIView.as_view()(request)
        assert response.status_code == 400
        assert not WalletLoginNonce.objects.exists()

    @pytest.mark.django_db
    def test_login_nonce_rejects_unsupported_chain(self):
        request = APIRequestFactory().post(
            "/login/nonce/", {"address": PROVEN, "chain": "solana"}, format="json"
        )
        response = WalletLoginNonceAPIView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_login_nonce_accepts_evm_address_shape(self):
        # Forward-looking: an EVM-shaped address is accepted at the nonce stage
        # (verify will report the chain is not yet enabled).
        request = APIRequestFactory().post(
            "/login/nonce/", {"address": EVM_ADDRESS, "chain": "evm"}, format="json"
        )
        response = WalletLoginNonceAPIView.as_view()(request)
        assert response.status_code == 200


class TestWalletLoginVerifyAPIView:
    """Testing class for :class:`WalletLoginVerifyAPIView`."""

    # # configuration
    def test_login_verify_is_anonymous_and_throttled(self):
        assert WalletLoginRateThrottle in WalletLoginVerifyAPIView.throttle_classes

    # # post - guard rails
    @pytest.mark.django_db
    def test_login_verify_rejects_missing_nonce(self):
        request = APIRequestFactory().post("/login/verify/", {}, format="json")
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert response.data["error"] == "Missing nonce"

    @pytest.mark.django_db
    def test_login_verify_rejects_unsupported_chain(self):
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n", "chain": "solana"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_login_verify_reports_chain_not_enabled(self, mocker):
        _patch_verifier(mocker, _FakeLoginVerifier(error=NotSupported("nope")))
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert "not yet enabled" in response.data["error"]

    @pytest.mark.django_db
    def test_login_verify_rejects_failed_proof(self, mocker):
        _patch_verifier(mocker, _FakeLoginVerifier(proven=None))
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert response.data["error"] == "Signature verification failed"

    @pytest.mark.django_db
    def test_login_verify_rejects_unknown_nonce(self, mocker):
        _patch_verifier(mocker, _FakeLoginVerifier(proven=PROVEN))
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "missing", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert response.data["error"] == "Invalid or used nonce"

    @pytest.mark.django_db
    def test_login_verify_rejects_nonce_for_other_address(self, mocker):
        # Nonce issued for a different address than the one the signature proves.
        WalletLoginNonce.objects.create(address=OTHER, chain="algorand", nonce="n1")
        _patch_verifier(mocker, _FakeLoginVerifier(proven=PROVEN))
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n1", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert response.data["error"] == "Invalid or used nonce"

    @pytest.mark.django_db
    def test_login_verify_rejects_expired_nonce(self, mocker):
        nonce = WalletLoginNonce.objects.create(
            address=PROVEN, chain="algorand", nonce="n2"
        )
        _patch_verifier(mocker, _FakeLoginVerifier(proven=PROVEN))
        mocker.patch.object(WalletLoginNonce, "is_expired", return_value=True)
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n2", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert response.data["error"] == "Nonce expired"
        assert nonce.pk is not None

    @pytest.mark.django_db
    def test_login_verify_rejects_lost_race(self, mocker):
        WalletLoginNonce.objects.create(address=PROVEN, chain="algorand", nonce="n3")
        _patch_verifier(mocker, _FakeLoginVerifier(proven=PROVEN))
        mocker.patch.object(WalletLoginNonce, "claim", return_value=False)
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n3", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 400
        assert response.data["error"] == "Nonce already used"

    @pytest.mark.django_db
    def test_login_verify_rejects_unlinked_wallet(self, mocker):
        WalletLoginNonce.objects.create(address=PROVEN, chain="algorand", nonce="n4")
        _patch_verifier(mocker, _FakeLoginVerifier(proven=PROVEN))
        perform = mocker.patch("walletauth.login_views._perform_login")
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n4", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 401
        assert "No account is linked" in response.data["error"]
        perform.assert_not_called()
        # the proof is consumed even though no account was linked
        assert WalletLoginNonce.objects.get(nonce="n4").used is True

    @pytest.mark.django_db
    def test_login_verify_reports_ambiguous_wallet(self, mocker):
        # Two accounts share the same verified address -> precise 409, not 401.
        for name in ("dup1", "dup2"):
            link_user(username=name)
        WalletLoginNonce.objects.create(address=PROVEN, chain="algorand", nonce="n6")
        _patch_verifier(mocker, _FakeLoginVerifier(proven=PROVEN))
        perform = mocker.patch("walletauth.login_views._perform_login")
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n6", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 409
        assert "more than one account" in response.data["error"]
        perform.assert_not_called()

    @pytest.mark.django_db
    def test_login_verify_logs_in_linked_account(self, mocker):
        user = link_user()
        WalletLoginNonce.objects.create(address=PROVEN, chain="algorand", nonce="n5")
        _patch_verifier(mocker, _FakeLoginVerifier(proven=PROVEN))
        perform = mocker.patch(
            "walletauth.login_views._perform_login", return_value="/home/"
        )
        request = APIRequestFactory().post(
            "/login/verify/", {"nonce": "n5", "chain": "algorand"}, format="json"
        )
        response = WalletLoginVerifyAPIView.as_view()(request)
        assert response.status_code == 200
        assert response.data == {"success": True, "redirect_url": "/home/"}
        assert perform.call_args.args[1] == user
        assert WalletLoginNonce.objects.get(nonce="n5").used is True


class TestIsValidChainAddress:
    """Testing class for :func:`is_valid_chain_address`."""

    def test_algorand_address_valid(self):
        from walletauth.login_views import is_valid_chain_address

        assert is_valid_chain_address("algorand", PROVEN) is True

    def test_evm_address_valid(self):
        from walletauth.login_views import is_valid_chain_address

        assert is_valid_chain_address("evm", EVM_ADDRESS) is True

    def test_unsupported_chain_is_invalid(self):
        from walletauth.login_views import is_valid_chain_address

        assert is_valid_chain_address("solana", PROVEN) is False


class TestPerformLogin:
    """Testing class for the allauth :func:`_perform_login` adapter."""

    def test_perform_login_delegates_to_allauth(self, mocker):
        import sys
        import types

        fake_account = types.ModuleType("allauth.account")
        fake_settings = types.ModuleType("allauth.account.app_settings")
        fake_settings.EMAIL_VERIFICATION = "optional"
        fake_utils = types.ModuleType("allauth.account.utils")
        fake_utils.perform_login = mocker.Mock(return_value=mocker.Mock(url="/dash/"))
        fake_account.app_settings = fake_settings
        fake_account.utils = fake_utils
        mocker.patch.dict(
            sys.modules,
            {
                "allauth": types.ModuleType("allauth"),
                "allauth.account": fake_account,
                "allauth.account.app_settings": fake_settings,
                "allauth.account.utils": fake_utils,
            },
        )
        from walletauth.login_views import _perform_login

        request = APIRequestFactory().post("/login/verify/")
        url = _perform_login(request, object())

        assert url == "/dash/"
        assert fake_utils.perform_login.called

    def test_perform_login_falls_back_to_login_redirect_url(self, mocker):
        import sys
        import types

        fake_account = types.ModuleType("allauth.account")
        fake_settings = types.ModuleType("allauth.account.app_settings")
        fake_settings.EMAIL_VERIFICATION = "optional"
        fake_utils = types.ModuleType("allauth.account.utils")
        # response without a usable .url -> view falls back to LOGIN_REDIRECT_URL
        fake_utils.perform_login = mocker.Mock(return_value=mocker.Mock(url=None))
        fake_account.app_settings = fake_settings
        fake_account.utils = fake_utils
        mocker.patch.dict(
            sys.modules,
            {
                "allauth": types.ModuleType("allauth"),
                "allauth.account": fake_account,
                "allauth.account.app_settings": fake_settings,
                "allauth.account.utils": fake_utils,
            },
        )
        from walletauth.login_views import _perform_login

        request = APIRequestFactory().post("/login/verify/")
        url = _perform_login(request, object())

        assert url == "/home/"
