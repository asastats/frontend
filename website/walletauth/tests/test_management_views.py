"""Testing module for :py:mod:`walletauth.management_views` and step-up."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.management import verify_step_up
from walletauth.management_views import ManageNonceAPIView
from walletauth.models import LinkedAddress, WalletNonce
from walletauth.verifiers import VERIFIERS, NotSupported

user_model = get_user_model()

EVM_PRIMARY = "0x52908400098527886e0f7030069857d2e4169ee7"
ALGO_SECOND = "BBBB4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


@pytest.fixture(autouse=True)
def _stub_permission_refresh(mocker):
    mocker.patch("core.models.Profile.check_votes_and_permission")


def make_user(username="owner"):
    return user_model.objects.create(username=username)


def evm_primary(profile, address=EVM_PRIMARY):
    profile.address = address
    profile.authorized = "p"
    profile.save()
    return LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address="LSIG" + address[2:],
        chain="evm",
        auth_method="evm_xchain",
        authorized="p",
        is_primary=True,
        login_enabled=True,
    )


def secondary(profile, address=ALGO_SECOND, *, login=False):
    return LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=address,
        chain="algorand",
        auth_method="algorand_wallet",
        authorized="s",
        is_primary=False,
        login_enabled=login,
    )


def post(view, data, user):
    request = APIRequestFactory().post("/manage/nonce/", data, format="json")
    force_authenticate(request, user=user)
    return view.as_view()(request)


def new_evm_key():
    from eth_account import Account

    return Account.create()


def sign_bound(acct, nonce, operation, target_id):
    """Sign the operation-bound challenge with an EVM key; return the 0x sig."""
    from eth_account.messages import encode_defunct

    bound = f"{nonce}:{operation}:{target_id}"
    raw = acct.sign_message(
        encode_defunct(text=WALLET_CONNECT_NONCE_PREFIX + bound)
    ).signature.hex()
    return raw if raw.startswith("0x") else "0x" + raw


class TestManageNonceAPIView:
    """Testing class for :class:`ManageNonceAPIView`."""

    @pytest.mark.django_db
    def test_nonce_bound_to_current_primary(self):
        user = make_user()
        evm_primary(user.profile)
        response = post(ManageNonceAPIView, {}, user)
        assert response.status_code == 200
        assert response.data["address"] == EVM_PRIMARY
        assert response.data["chain"] == "evm"
        assert WalletNonce.objects.get(nonce=response.data["nonce"]).user == user

    @pytest.mark.django_db
    def test_nonce_requires_a_primary(self):
        user = make_user()
        response = post(ManageNonceAPIView, {}, user)
        assert response.status_code == 400

    def test_nonce_requires_authentication(self):
        request = APIRequestFactory().post("/manage/nonce/", {}, format="json")
        assert ManageNonceAPIView.as_view()(request).status_code in (401, 403)


class TestVerifyStepUp:
    """Testing class for :func:`walletauth.management.verify_step_up`."""

    def _primary_with_nonce(self, user, nonce="n1"):
        acct = new_evm_key()
        evm_primary(user.profile, address=acct.address.lower())
        sec = secondary(user.profile, login=False)
        WalletNonce.objects.create(
            user=user, address=acct.address.lower(), nonce=nonce, chain="evm"
        )
        return acct, sec

    @pytest.mark.django_db
    def test_success_claims_nonce(self):
        user = make_user()
        acct, sec = self._primary_with_nonce(user)
        sig = sign_bound(acct, "n1", "set_login", sec.id)
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="n1",
            payload={"signature": sig},
        )
        assert err is None
        assert WalletNonce.objects.get(nonce="n1").used is True

    @pytest.mark.django_db
    def test_signature_bound_to_operation(self):
        # Signed to enable login; cannot be replayed to set primary.
        user = make_user()
        acct, sec = self._primary_with_nonce(user)
        sig = sign_bound(acct, "n1", "set_login", sec.id)
        err = verify_step_up(
            user=user,
            operation="set_primary",
            target_id=sec.id,
            nonce="n1",
            payload={"signature": sig},
        )
        assert err == "Step-up signature did not match your primary address"
        assert WalletNonce.objects.get(nonce="n1").used is False

    @pytest.mark.django_db
    def test_signature_bound_to_target(self):
        user = make_user()
        acct, sec = self._primary_with_nonce(user)
        sig = sign_bound(acct, "n1", "set_login", sec.id + 999)
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="n1",
            payload={"signature": sig},
        )
        assert err == "Step-up signature did not match your primary address"

    @pytest.mark.django_db
    def test_wrong_signer_rejected(self):
        user = make_user()
        acct, sec = self._primary_with_nonce(user)
        other = new_evm_key()
        sig = sign_bound(other, "n1", "set_login", sec.id)
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="n1",
            payload={"signature": sig},
        )
        assert err == "Step-up signature did not match your primary address"

    @pytest.mark.django_db
    def test_garbage_signature_rejected(self):
        user = make_user()
        acct, sec = self._primary_with_nonce(user)
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="n1",
            payload={"signature": "0x00"},
        )
        assert err == "Step-up signature did not match your primary address"

    @pytest.mark.django_db
    def test_no_primary(self):
        user = make_user()
        err = verify_step_up(
            user=user,
            operation="set_primary",
            target_id=1,
            nonce="n1",
            payload={},
        )
        assert err == "No primary address"

    @pytest.mark.django_db
    def test_missing_nonce(self):
        user = make_user()
        evm_primary(user.profile)
        err = verify_step_up(
            user=user,
            operation="set_primary",
            target_id=1,
            nonce="",
            payload={},
        )
        assert err == "Missing step-up signature"

    @pytest.mark.django_db
    def test_unsupported_chain(self):
        user = make_user()
        user.profile.address = "x"
        user.profile.save()
        LinkedAddress.objects.create(
            profile=user.profile,
            address="x",
            canonical_address="x",
            chain="solana",
            auth_method="other",
            is_primary=True,
            login_enabled=True,
        )
        err = verify_step_up(
            user=user,
            operation="set_primary",
            target_id=1,
            nonce="n1",
            payload={},
        )
        assert err == "Unsupported chain"

    @pytest.mark.django_db
    def test_not_supported_bubbles_message(self, mocker):
        user = make_user()
        acct, sec = self._primary_with_nonce(user)
        mocker.patch.object(
            VERIFIERS["evm"], "recover", side_effect=NotSupported("nope")
        )
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="n1",
            payload={"signature": "0x00"},
        )
        assert err == "nope"

    @pytest.mark.django_db
    def test_nonce_not_in_db(self):
        user = make_user()
        acct = new_evm_key()
        evm_primary(user.profile, address=acct.address.lower())
        sec = secondary(user.profile, login=False)
        sig = sign_bound(acct, "ghost", "set_login", sec.id)
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="ghost",
            payload={"signature": sig},
        )
        assert err == "Step-up challenge not found or already used"

    @pytest.mark.django_db
    def test_expired_nonce(self):
        user = make_user()
        acct, sec = self._primary_with_nonce(user, nonce="old")
        WalletNonce.objects.filter(nonce="old").update(
            created_at=timezone.now() - WalletNonce.NONCE_TTL * 2
        )
        sig = sign_bound(acct, "old", "set_login", sec.id)
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="old",
            payload={"signature": sig},
        )
        assert err == "Step-up challenge expired or already used"

    @pytest.mark.django_db
    def test_claim_race_lost(self, mocker):
        user = make_user()
        acct, sec = self._primary_with_nonce(user)
        sig = sign_bound(acct, "n1", "set_login", sec.id)
        mocker.patch.object(WalletNonce, "claim", return_value=False)
        err = verify_step_up(
            user=user,
            operation="set_login",
            target_id=sec.id,
            nonce="n1",
            payload={"signature": sig},
        )
        assert err == "Step-up challenge expired or already used"
