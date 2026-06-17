"""Testing module for :py:mod:`core.views_connected_addresses`.

``render`` and ``reverse`` are patched so these stay focused on the view logic
(no template/URLconf coupling); the management services run for real against the
DB, and only :func:`walletauth.management.verify_step_up` -- exhaustively tested
in walletauth -- is stubbed to drive the step-up branches.
"""

import json

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory

from core import views_connected_addresses as views
from utils.constants.core import ALGORAND_WALLETS
from walletauth.models import LinkedAddress

EVM_PRIMARY = "0x52908400098527886e0f7030069857d2e4169ee7"
ALGO_SECOND = "BBBB4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


@pytest.fixture(autouse=True)
def _stub_permission_refresh(mocker):
    mocker.patch("core.models.Profile.check_votes_and_permission")


@pytest.fixture(autouse=True)
def _fake_render(mocker):
    """Make ``render`` return a real, mutable response without templates."""
    return mocker.patch(
        "core.views_connected_addresses.render",
        side_effect=lambda request, template, context=None, **kw: HttpResponse(
            b"<partial>"
        ),
    )


def make_user(username="owner"):
    return User.objects.create(username=username)


def primary(profile, address=EVM_PRIMARY):
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


def action(user, data):
    request = RequestFactory().post("/profile/addresses/action/", data)
    request.user = user
    return views.profile_addresses_action(request)


def _error_of(response):
    """Return the wallet-error message from an HX-Trigger header, or None."""
    trigger = response.headers.get("HX-Trigger")
    return json.loads(trigger)["wallet-error"] if trigger else None


class TestProfileAddresses:
    """Testing class for :func:`profile_addresses` and :func:`profile_link_address`."""

    @pytest.mark.django_db
    def test_renders_page_with_rows_primary_first(self, mocker, _fake_render):
        mocker.patch("core.views_connected_addresses.reverse", return_value="/link/")
        user = make_user()
        primary(user.profile)
        secondary(user.profile, login=True)
        request = RequestFactory().get("/profile/addresses/")
        request.user = user
        response = views.profile_addresses(request)
        assert response.status_code == 200
        _, _, context = _fake_render.call_args.args
        assert context["link_address_url"] == "/link/"
        assert "wallet_connect_project_id" in context
        rows = context["addresses"]
        assert len(rows) == 2
        assert rows[0]["is_primary"] is True
        assert rows[0]["address"] == EVM_PRIMARY
        assert rows[1]["is_primary"] is False

    @pytest.mark.django_db
    def test_link_page_provides_wallets(self, _fake_render):
        user = make_user()
        request = RequestFactory().get("/profile/addresses/link/")
        request.user = user
        response = views.profile_link_address(request)
        assert response.status_code == 200
        template = _fake_render.call_args.args[1]
        context = _fake_render.call_args.args[2]
        assert template == "profile_link_address.html"
        assert context["wallets"] == ALGORAND_WALLETS
        assert "wallet_connect_project_id" in context


class TestProfileAddressesAction:
    """Testing class for :func:`profile_addresses_action`."""

    @pytest.mark.django_db
    def test_unknown_operation(self):
        user = make_user()
        primary(user.profile)
        response = action(user, {"operation": "nuke", "target_id": 1})
        assert _error_of(response) == "Unknown operation"
        assert response.headers["Cache-Control"] == "private, no-store"
        assert response.headers["HX-Reswap"] == "none"

    @pytest.mark.django_db
    def test_target_not_found(self):
        user = make_user()
        primary(user.profile)
        response = action(user, {"operation": "remove", "target_id": 999999})
        assert _error_of(response) == "Address not found"

    @pytest.mark.django_db
    def test_target_id_not_an_int(self):
        user = make_user()
        primary(user.profile)
        response = action(user, {"operation": "remove", "target_id": "abc"})
        assert _error_of(response) == "Address not found"

    @pytest.mark.django_db
    def test_remove_secondary_succeeds(self):
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile)
        response = action(user, {"operation": "remove", "target_id": sec.id})
        assert _error_of(response) is None
        assert not LinkedAddress.objects.filter(id=sec.id).exists()

    @pytest.mark.django_db
    def test_disable_login_needs_no_step_up(self, mocker):
        spy = mocker.patch("core.views_connected_addresses.verify_step_up")
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile, login=True)
        response = action(
            user,
            {"operation": "set_login", "target_id": sec.id, "enabled": "false"},
        )
        assert _error_of(response) is None
        sec.refresh_from_db()
        assert sec.login_enabled is False
        spy.assert_not_called()

    @pytest.mark.django_db
    def test_enable_login_step_up_succeeds(self, mocker):
        mocker.patch("core.views_connected_addresses.verify_step_up", return_value=None)
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile, login=False)
        response = action(
            user,
            {
                "operation": "set_login",
                "target_id": sec.id,
                "enabled": "true",
                "nonce": "n",
            },
        )
        assert _error_of(response) is None
        sec.refresh_from_db()
        assert sec.login_enabled is True

    @pytest.mark.django_db
    def test_enable_login_step_up_fails(self, mocker):
        mocker.patch(
            "core.views_connected_addresses.verify_step_up",
            return_value="Step-up signature did not match your primary address",
        )
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile, login=False)
        response = action(
            user,
            {"operation": "set_login", "target_id": sec.id, "enabled": "true"},
        )
        assert "did not match" in _error_of(response)
        sec.refresh_from_db()
        assert sec.login_enabled is False

    @pytest.mark.django_db
    def test_set_primary_step_up_succeeds(self, mocker):
        mocker.patch("core.views_connected_addresses.verify_step_up", return_value=None)
        user = make_user()
        primary(user.profile)
        sec = secondary(user.profile)
        response = action(user, {"operation": "set_primary", "target_id": sec.id})
        assert _error_of(response) is None
        sec.refresh_from_db()
        assert sec.is_primary is True

    @pytest.mark.django_db
    def test_cannot_disable_primary_login(self):
        user = make_user()
        prim = primary(user.profile)
        response = action(
            user,
            {"operation": "set_login", "target_id": prim.id, "enabled": "false"},
        )
        assert _error_of(response) is not None
        prim.refresh_from_db()
        assert prim.login_enabled is True

    @pytest.mark.django_db
    def test_cannot_remove_primary(self):
        user = make_user()
        prim = primary(user.profile)
        response = action(user, {"operation": "remove", "target_id": prim.id})
        assert _error_of(response) is not None
        assert LinkedAddress.objects.filter(id=prim.id).exists()
