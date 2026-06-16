"""Testing module for :py:mod:`walletauth.management_views` module."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from utils.constants.core import WALLET_CONNECT_NONCE_PREFIX
from walletauth.management_views import (
    ManageAddressAPIView,
    ManageNonceAPIView,
    WalletAddressesAPIView,
)
from walletauth.models import LinkedAddress, WalletNonce

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
    request = APIRequestFactory().post("/manage/", data, format="json")
    force_authenticate(request, user=user)
    return view.as_view()(request)


class TestWalletAddressesAPIView:
    """Testing class for :class:`WalletAddressesAPIView`."""

    @pytest.mark.django_db
    def test_lists_caller_addresses_primary_first(self):
        user = make_user()
        evm_primary(user.profile)
        secondary(user.profile, login=True)
        request = APIRequestFactory().get("/manage/addresses/")
        force_authenticate(request, user=user)
        response = WalletAddressesAPIView.as_view()(request)
        assert response.status_code == 200
        rows = response.data["addresses"]
        assert len(rows) == 2
        assert rows[0]["is_primary"] is True
        assert rows[0]["address"] == EVM_PRIMARY
        assert rows[1]["is_primary"] is False

    @pytest.mark.django_db
    def test_scoped_to_caller(self):
        owner = make_user("owner")
        evm_primary(owner.profile)
        other = make_user("other")
        evm_primary(other.profile, address="0x" + "a" * 40)
        request = APIRequestFactory().get("/manage/addresses/")
        force_authenticate(request, user=other)
        response = WalletAddressesAPIView.as_view()(request)
        addresses = {row["address"] for row in response.data["addresses"]}
        assert addresses == {"0x" + "a" * 40}

    def test_requires_authentication(self):
        request = APIRequestFactory().get("/manage/addresses/")
        assert WalletAddressesAPIView.as_view()(request).status_code in (401, 403)


def evm_step_up(user, nonce):
    """Create a step-up nonce and a valid signature from a fresh EVM key.

    Returns (signature, primary_address) so a primary can be created at that
    address (the recovered signer must equal the current primary).
    """
    from eth_account import Account
    from eth_account.messages import encode_defunct

    acct = Account.create()
    signed = acct.sign_message(encode_defunct(text=WALLET_CONNECT_NONCE_PREFIX + nonce))
    raw = signed.signature.hex()
    return (raw if raw.startswith("0x") else "0x" + raw), acct.address.lower()


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


class TestManageAddressAPIView:
    """Testing class for :class:`ManageAddressAPIView`."""

    # # validation / scoping
    @pytest.mark.django_db
    def test_unknown_operation_rejected(self):
        user = make_user()
        evm_primary(user.profile)
        response = post(ManageAddressAPIView, {"operation": "nuke"}, user)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_cannot_target_another_users_address(self):
        owner = make_user("owner")
        evm_primary(owner.profile)
        victim = make_user("victim")
        victim_secondary = secondary(victim.profile)
        attacker = make_user("attacker")
        evm_primary(attacker.profile, address="0x" + "a" * 40)
        # Attacker tries to remove the victim's address by id.
        response = post(
            ManageAddressAPIView,
            {"operation": "remove", "target_id": victim_secondary.id},
            attacker,
        )
        assert response.status_code == 404
        assert LinkedAddress.objects.filter(pk=victim_secondary.pk).exists()

    # # no step-up: remove / disable
    @pytest.mark.django_db
    def test_remove_secondary_without_step_up(self):
        user = make_user()
        evm_primary(user.profile)
        sec = secondary(user.profile)
        response = post(
            ManageAddressAPIView,
            {"operation": "remove", "target_id": sec.id},
            user,
        )
        assert response.status_code == 200
        assert not LinkedAddress.objects.filter(pk=sec.pk).exists()

    @pytest.mark.django_db
    def test_remove_primary_rejected(self):
        user = make_user()
        prim = evm_primary(user.profile)
        response = post(
            ManageAddressAPIView,
            {"operation": "remove", "target_id": prim.id},
            user,
        )
        assert response.status_code == 400
        assert LinkedAddress.objects.filter(pk=prim.pk).exists()

    @pytest.mark.django_db
    def test_disable_login_without_step_up(self):
        user = make_user()
        evm_primary(user.profile)
        sec = secondary(user.profile, login=True)
        response = post(
            ManageAddressAPIView,
            {"operation": "set_login", "target_id": sec.id, "enabled": False},
            user,
        )
        assert response.status_code == 200
        sec.refresh_from_db()
        assert sec.login_enabled is False

    @pytest.mark.django_db
    def test_cannot_disable_primary_login(self):
        user = make_user()
        prim = evm_primary(user.profile)
        response = post(
            ManageAddressAPIView,
            {"operation": "set_login", "target_id": prim.id, "enabled": False},
            user,
        )
        assert response.status_code == 400

    # # step-up: enable login
    @pytest.mark.django_db
    def test_enable_login_requires_step_up_and_succeeds(self):
        user = make_user()
        signature, addr = evm_step_up(user, "stepup1")
        evm_primary(user.profile, address=addr)
        sec = secondary(user.profile, login=False)
        WalletNonce.objects.create(
            user=user, address=addr, nonce="stepup1", chain="evm"
        )
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_login",
                "target_id": sec.id,
                "enabled": True,
                "nonce": "stepup1",
                "chain": "evm",
                "signature": signature,
            },
            user,
        )
        assert response.status_code == 200
        sec.refresh_from_db()
        assert sec.login_enabled is True

    @pytest.mark.django_db
    def test_enable_login_rejected_without_signature(self):
        user = make_user()
        evm_primary(user.profile)
        sec = secondary(user.profile, login=False)
        response = post(
            ManageAddressAPIView,
            {"operation": "set_login", "target_id": sec.id, "enabled": True},
            user,
        )
        assert response.status_code == 400
        sec.refresh_from_db()
        assert sec.login_enabled is False

    @pytest.mark.django_db
    def test_step_up_rejected_for_wrong_signer(self):
        # A valid signature, but from a key that is not the current primary.
        user = make_user()
        signature, other_addr = evm_step_up(user, "stepup2")
        evm_primary(user.profile, address="0x" + "c" * 40)  # different primary
        sec = secondary(user.profile, login=False)
        WalletNonce.objects.create(
            user=user, address="0x" + "c" * 40, nonce="stepup2", chain="evm"
        )
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_login",
                "target_id": sec.id,
                "enabled": True,
                "nonce": "stepup2",
                "chain": "evm",
                "signature": signature,
            },
            user,
        )
        assert response.status_code == 401
        sec.refresh_from_db()
        assert sec.login_enabled is False

    # # step-up: set primary
    @pytest.mark.django_db
    def test_set_primary_with_step_up(self):
        user = make_user()
        signature, addr = evm_step_up(user, "stepup3")
        evm_primary(user.profile, address=addr)
        sec = secondary(user.profile)
        WalletNonce.objects.create(
            user=user, address=addr, nonce="stepup3", chain="evm"
        )
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_primary",
                "target_id": sec.id,
                "nonce": "stepup3",
                "chain": "evm",
                "signature": signature,
            },
            user,
        )
        assert response.status_code == 200
        sec.refresh_from_db()
        assert sec.is_primary is True
        user.profile.refresh_from_db()
        assert user.profile.address == ALGO_SECOND

    @pytest.mark.django_db
    def test_set_primary_rejected_without_step_up(self):
        user = make_user()
        evm_primary(user.profile)
        sec = secondary(user.profile)
        response = post(
            ManageAddressAPIView,
            {"operation": "set_primary", "target_id": sec.id},
            user,
        )
        assert response.status_code == 400
        sec.refresh_from_db()
        assert sec.is_primary is False

    # # step-up defensive branches
    @pytest.mark.django_db
    def test_step_up_nonce_not_found(self):
        user = make_user()
        signature, addr = evm_step_up(user, "n1")
        evm_primary(user.profile, address=addr)
        sec = secondary(user.profile)
        # Valid signature matching the primary, but no challenge was issued.
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_login",
                "target_id": sec.id,
                "enabled": True,
                "nonce": "n1",
                "chain": "evm",
                "signature": signature,
            },
            user,
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_step_up_nonce_expired(self, mocker):
        user = make_user()
        signature, addr = evm_step_up(user, "n2")
        evm_primary(user.profile, address=addr)
        sec = secondary(user.profile)
        WalletNonce.objects.create(user=user, address=addr, nonce="n2", chain="evm")
        mocker.patch("walletauth.models.WalletNonce.is_expired", return_value=True)
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_login",
                "target_id": sec.id,
                "enabled": True,
                "nonce": "n2",
                "chain": "evm",
                "signature": signature,
            },
            user,
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_step_up_unsupported_primary_chain(self):
        user = make_user()
        # A primary on a chain with no registered verifier.
        LinkedAddress.objects.create(
            profile=user.profile,
            address="solana-addr",
            canonical_address="solana-addr",
            chain="solana",
            auth_method="x",
            is_primary=True,
            login_enabled=True,
        )
        sec = secondary(user.profile)
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_login",
                "target_id": sec.id,
                "enabled": True,
                "nonce": "n",
                "chain": "solana",
                "signature": "x",
            },
            user,
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_step_up_verifier_reports_not_supported(self, mocker):
        from walletauth.verifiers import NotSupported

        class _Raises:
            def recover(self, **kwargs):
                raise NotSupported("nope")

        user = make_user()
        evm_primary(user.profile)
        sec = secondary(user.profile)
        WalletNonce.objects.create(
            user=user, address=EVM_PRIMARY, nonce="n", chain="evm"
        )
        mocker.patch.dict("walletauth.management_views.VERIFIERS", {"evm": _Raises()})
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_login",
                "target_id": sec.id,
                "enabled": True,
                "nonce": "n",
                "chain": "evm",
                "signature": "x",
            },
            user,
        )
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_step_up_no_primary(self):
        # A secondary with no primary on the account: step-up can't proceed.
        user = make_user()
        sec = secondary(user.profile)
        response = post(
            ManageAddressAPIView,
            {
                "operation": "set_primary",
                "target_id": sec.id,
                "nonce": "n",
                "chain": "evm",
                "signature": "x",
            },
            user,
        )
        assert response.status_code == 400
