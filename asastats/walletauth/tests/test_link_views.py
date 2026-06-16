"""Testing module for :py:mod:`walletauth.link_views` module."""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import NoReverseMatch
from rest_framework.test import APIRequestFactory, force_authenticate

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.link_views import (
    WalletLinkNonceAPIView,
    WalletLinkVerifyAPIView,
    _link_redirect_url,
)
from walletauth.models import LinkedAddress, WalletNonce

user_model = get_user_model()

EVM_ADDRESS = "0x52908400098527886E0F7030069857D2E4169EE7"
OLD_ALGORAND = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


def make_user(username="linker"):
    return user_model.objects.create(username=username)


def evm_sign(message):
    from eth_account import Account
    from eth_account.messages import encode_defunct

    acct = Account.create()
    signed = acct.sign_message(encode_defunct(text=message))
    raw = signed.signature.hex()
    return acct.address.lower(), (raw if raw.startswith("0x") else "0x" + raw)


def post(view, data, user):
    request = APIRequestFactory().post("/link/", data, format="json")
    force_authenticate(request, user=user)
    return view.as_view()(request)


class TestWalletLinkNonceAPIView:
    """Testing class for :class:`WalletLinkNonceAPIView`."""

    # # post
    @pytest.mark.django_db
    def test_link_nonce_creates_user_bound_lowercased_nonce(self):
        user = make_user()
        response = post(
            WalletLinkNonceAPIView, {"address": EVM_ADDRESS, "chain": "evm"}, user
        )
        assert response.status_code == 200
        assert response.data["prefix"] == WALLET_CONNECT_NONCE_PREFIX
        nonce = WalletNonce.objects.get(nonce=response.data["nonce"])
        assert nonce.user == user
        assert nonce.address == EVM_ADDRESS.lower()
        assert nonce.chain == "evm"

    @pytest.mark.django_db
    def test_link_nonce_rejects_invalid_address(self):
        user = make_user()
        response = post(
            WalletLinkNonceAPIView, {"address": "nope", "chain": "evm"}, user
        )
        assert response.status_code == 400
        assert not WalletNonce.objects.exists()

    @pytest.mark.django_db
    def test_link_nonce_rejects_unsupported_chain(self):
        user = make_user()
        response = post(
            WalletLinkNonceAPIView, {"address": EVM_ADDRESS, "chain": "solana"}, user
        )
        assert response.status_code == 400

    def test_link_nonce_requires_authentication(self):
        request = APIRequestFactory().post(
            "/link/nonce/", {"address": EVM_ADDRESS, "chain": "evm"}, format="json"
        )
        response = WalletLinkNonceAPIView.as_view()(request)
        assert response.status_code in (401, 403)


class TestWalletLinkVerifyAPIView:
    """Testing class for :class:`WalletLinkVerifyAPIView`."""

    # # guard rails
    @pytest.mark.django_db
    def test_link_verify_missing_nonce(self):
        response = post(WalletLinkVerifyAPIView, {"chain": "evm"}, make_user())
        assert response.status_code == 400
        assert response.data["error"] == "Missing nonce"

    @pytest.mark.django_db
    def test_link_verify_unsupported_chain(self):
        response = post(
            WalletLinkVerifyAPIView, {"nonce": "n", "chain": "solana"}, make_user()
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_link_verify_bad_signature(self):
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "n", "chain": "evm", "signature": "0xdead"},
            make_user(),
        )
        assert response.status_code == 400
        assert response.data["error"] == "Signature verification failed"

    @pytest.mark.django_db
    def test_link_verify_unknown_nonce(self):
        # Valid signature, but no matching user-bound nonce exists.
        _, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "missing")
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "missing", "chain": "evm", "signature": sig},
            make_user(),
        )
        assert response.status_code == 400
        assert response.data["error"] == "Nonce not found or already used"

    @pytest.mark.django_db
    def test_link_verify_rejects_other_users_nonce(self):
        # The nonce is bound to a different user than the one signing in.
        owner = make_user("owner")
        attacker = make_user("attacker")
        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "shared")
        WalletNonce.objects.create(
            user=owner, address=evm_addr, nonce="shared", chain="evm"
        )
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "shared", "chain": "evm", "signature": sig},
            attacker,
        )
        assert response.status_code == 400
        assert response.data["error"] == "Nonce not found or already used"

    @pytest.mark.django_db
    def test_link_verify_expired_nonce(self, mocker):
        user = make_user()
        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "exp")
        WalletNonce.objects.create(
            user=user, address=evm_addr, nonce="exp", chain="evm"
        )
        mocker.patch.object(WalletNonce, "is_expired", return_value=True)
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "exp", "chain": "evm", "signature": sig},
            user,
        )
        assert response.status_code == 400
        assert response.data["error"] == "Nonce expired"

    @pytest.mark.django_db
    def test_link_verify_lost_race(self, mocker):
        user = make_user()
        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "race")
        WalletNonce.objects.create(
            user=user, address=evm_addr, nonce="race", chain="evm"
        )
        mocker.patch.object(WalletNonce, "claim", return_value=False)
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "race", "chain": "evm", "signature": sig},
            user,
        )
        assert response.status_code == 400
        assert response.data["error"] == "Nonce already used"

    @pytest.mark.django_db
    def test_link_verify_unsupported_when_verifier_missing(self, mocker):
        # A chain that is linkable but has no registered verifier (defensive).
        mocker.patch("walletauth.link_views.LINKABLE_CHAINS", {"ghost"})
        response = post(
            WalletLinkVerifyAPIView, {"nonce": "n", "chain": "ghost"}, make_user()
        )
        assert response.status_code == 400
        assert response.data["error"] == "Unsupported chain"

    @pytest.mark.django_db
    def test_link_verify_reports_not_supported(self, mocker):
        from walletauth.verifiers import NotSupported

        class _Raises:
            def recover(self, **kwargs):
                raise NotSupported("link for this chain is not yet enabled")

        mocker.patch.dict("walletauth.link_views.VERIFIERS", {"evm": _Raises()})
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "n", "chain": "evm", "signature": "0x00"},
            make_user(),
        )
        assert response.status_code == 400
        assert "not yet enabled" in response.data["error"]

    # # success
    @pytest.mark.django_db
    def test_link_verify_stores_address_and_authorizes(self, mocker):
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        mocker.patch(
            "walletauth.addresses.check_evm_address",
            side_effect=lambda a, c: "LSIG" + a[2:].upper(),
        )
        user = make_user("newlink")
        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "ok")
        WalletNonce.objects.create(user=user, address=evm_addr, nonce="ok", chain="evm")
        provider = mocker.patch("core.models.get_permission_provider").return_value
        provider.votes_and_permission.return_value = (0, 0)
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "ok", "chain": "evm", "signature": sig},
            user,
        )
        assert response.status_code == 200
        assert response.data["success"] is True
        assert response.data["is_primary"] is True
        assert response.data["permission_pending"] is False
        user.profile.refresh_from_db()
        assert user.profile.address == evm_addr
        assert user.profile.authorized == "ok"
        assert user.profile.auth_method == "evm_xchain"
        assert WalletNonce.objects.get(nonce="ok").used is True

    @pytest.mark.django_db
    def test_link_verify_redirect_url_honours_setting(self, mocker):
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        mocker.patch(
            "walletauth.addresses.check_evm_address",
            side_effect=lambda a, c: "LSIG" + a[2:].upper(),
        )
        user = make_user("redir")
        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "rd")
        WalletNonce.objects.create(user=user, address=evm_addr, nonce="rd", chain="evm")
        provider = mocker.patch("core.models.get_permission_provider").return_value
        provider.votes_and_permission.return_value = (0, 0)
        with override_settings(WALLET_LINK_REDIRECT_URL="/account/addresses/"):
            response = post(
                WalletLinkVerifyAPIView,
                {"nonce": "rd", "chain": "evm", "signature": sig},
                user,
            )
        assert response.data["redirect_url"] == "/account/addresses/"

    @pytest.mark.django_db
    def test_link_verify_adds_secondary_when_primary_exists(self, mocker):
        # A profile that already has an authorized primary: linking another
        # address now adds a non-privileged secondary and leaves the primary
        # (and therefore permission) untouched -- it no longer overwrites it.
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        mocker.patch(
            "walletauth.addresses.check_evm_address",
            side_effect=lambda a, c: "LSIG" + a[2:].upper(),
        )
        user = make_user("switcher")
        user.profile.address = OLD_ALGORAND
        user.profile.authorized = "old-proof"
        user.profile.save()

        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "second")
        WalletNonce.objects.create(
            user=user, address=evm_addr, nonce="second", chain="evm"
        )
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "second", "chain": "evm", "signature": sig},
            user,
        )
        assert response.status_code == 200
        assert response.data["is_primary"] is False
        user.profile.refresh_from_db()
        # Primary identity and authorization are preserved.
        assert user.profile.address == OLD_ALGORAND
        assert user.profile.authorized == "old-proof"
        secondary = LinkedAddress.objects.get(address=evm_addr)
        assert secondary.is_primary is False
        assert secondary.login_enabled is False

    @pytest.mark.django_db
    def test_link_verify_rejects_when_secondary_limit_reached(self, mocker):
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        mocker.patch(
            "walletauth.addresses.check_evm_address",
            side_effect=lambda a, c: "LSIG" + a[2:].upper(),
        )
        user = make_user("capped")
        user.profile.address = OLD_ALGORAND  # has a primary
        user.profile.save()
        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "cap")
        WalletNonce.objects.create(
            user=user, address=evm_addr, nonce="cap", chain="evm"
        )
        with override_settings(MAX_SECONDARY_ADDRESSES=0):
            response = post(
                WalletLinkVerifyAPIView,
                {"nonce": "cap", "chain": "evm", "signature": sig},
                user,
            )
        assert response.status_code == 400
        assert "maximum" in response.data["error"].lower()

    @pytest.mark.django_db
    def test_link_verify_supports_algorand_secondary(self, mocker):
        # Algorand secondaries link through the same flow; recover is mocked
        # (the verifier itself is covered in test_verifiers).
        user = make_user("algolink")
        user.profile.address = OLD_ALGORAND  # already has a primary
        user.profile.save()
        proven = "ZZZZ4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
        WalletNonce.objects.create(
            user=user, address=proven, nonce="algo2", chain="algorand"
        )

        class _Verifier:
            def recover(self, **kwargs):
                return proven

        mocker.patch.dict("walletauth.link_views.VERIFIERS", {"algorand": _Verifier()})
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "algo2", "chain": "algorand", "signature": "x"},
            user,
        )
        assert response.status_code == 200
        assert response.data["is_primary"] is False
        row = LinkedAddress.objects.get(address=proven)
        assert row.chain == "algorand"
        assert row.canonical_address == proven  # native: canonical is itself
        mocker.patch("walletauth.addresses.algod_instance", return_value=object())
        mocker.patch(
            "walletauth.addresses.check_evm_address",
            side_effect=lambda a, c: "LSIG" + a[2:].upper(),
        )
        # Another account already holds the canonical of this EVM address.
        evm_addr, sig = evm_sign(WALLET_CONNECT_NONCE_PREFIX + "dup")
        other = make_user("holder")
        LinkedAddress.objects.create(
            profile=other.profile,
            address=evm_addr,
            canonical_address="LSIG" + evm_addr[2:].upper(),
            chain="evm",
            auth_method="evm_xchain",
            is_primary=True,
            login_enabled=True,
        )
        user = make_user("claimer")
        user.profile.address = OLD_ALGORAND  # already has a primary
        user.profile.save()
        WalletNonce.objects.create(
            user=user, address=evm_addr, nonce="dup", chain="evm"
        )
        response = post(
            WalletLinkVerifyAPIView,
            {"nonce": "dup", "chain": "evm", "signature": sig},
            user,
        )
        assert response.status_code == 409


class TestLinkRedirectUrl:
    """Testing class for :func:`walletauth.link_views._link_redirect_url`."""

    def test_path_setting_used_verbatim(self):
        with override_settings(WALLET_LINK_REDIRECT_URL="/account/addresses/"):
            assert _link_redirect_url() == "/account/addresses/"

    def test_name_setting_is_reversed(self):
        with override_settings(WALLET_LINK_REDIRECT_URL="profile"):
            assert _link_redirect_url() == "/profile/"

    def test_unresolvable_name_setting_returned_as_is(self):
        with override_settings(WALLET_LINK_REDIRECT_URL="no_such_url_name"):
            assert _link_redirect_url() == "no_such_url_name"

    def test_default_prefers_connected_addresses(self, mocker):
        mocker.patch(
            "walletauth.link_views.reverse",
            side_effect=lambda name: (
                "/account/addresses/" if name == "profile_addresses" else "/profile/"
            ),
        )
        assert _link_redirect_url() == "/account/addresses/"

    def test_default_falls_back_to_root_when_nothing_resolves(self, mocker):
        mocker.patch("walletauth.link_views.reverse", side_effect=NoReverseMatch)
        assert _link_redirect_url() == "/"
