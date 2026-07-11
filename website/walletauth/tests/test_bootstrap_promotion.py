"""Tests for the first-primary bootstrap waiver (Issue: legacy profile.address)."""

import json

import pytest
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory

from core import views_connected_addresses as views
from walletauth.management import is_bootstrap_promotion
from walletauth.models import LinkedAddress

ALGO_A = "AAAA4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"
ALGO_B = "BBBB4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


@pytest.fixture(autouse=True)
def _stub_permission(mocker):
    mocker.patch("core.models.Profile.check_votes_and_permission")


def user_with_address(address=""):
    u = User.objects.create(username="u")
    p = u.profile
    p.address = address
    p.save()
    return u


def linked(profile, address, *, chain="algorand", primary=False, login=False):
    return LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=address,
        chain=chain,
        auth_method="algorand_wallet",
        authorized="proof",
        is_primary=primary,
        login_enabled=login or primary,
    )


class TestIsBootstrapPromotion:
    @pytest.mark.django_db
    def test_true_no_primary_and_target_is_profile_address(self):
        u = user_with_address(ALGO_A)
        assert is_bootstrap_promotion(u.profile, linked(u.profile, ALGO_A)) is True

    @pytest.mark.django_db
    def test_false_when_target_differs_from_profile_address(self):
        u = user_with_address(ALGO_A)
        assert is_bootstrap_promotion(u.profile, linked(u.profile, ALGO_B)) is False

    @pytest.mark.django_db
    def test_false_when_profile_address_empty(self):
        u = user_with_address("")
        assert is_bootstrap_promotion(u.profile, linked(u.profile, ALGO_A)) is False

    @pytest.mark.django_db
    def test_false_when_a_primary_already_exists(self):
        u = user_with_address(ALGO_A)
        linked(u.profile, ALGO_B, primary=True)  # a primary exists
        assert is_bootstrap_promotion(u.profile, linked(u.profile, ALGO_A)) is False


class TestActionBootstrap:
    @pytest.fixture(autouse=True)
    def _fake_render(self, mocker):
        return mocker.patch(
            "core.views_connected_addresses.render",
            side_effect=lambda req, tmpl, ctx=None, **k: HttpResponse(b"<ul></ul>"),
        )

    def _action(self, user, data):
        request = RequestFactory().post("/x/", data)
        request.user = user
        return views.profile_addresses_action(request)

    @pytest.mark.django_db
    def test_set_primary_bootstraps_without_step_up(self, mocker):
        spy = mocker.patch("core.views_connected_addresses.verify_step_up")
        u = user_with_address(ALGO_A)
        row = linked(u.profile, ALGO_A)  # non-primary, matches profile.address
        resp = self._action(u, {"operation": "set_primary", "target_id": row.id})
        assert "HX-Trigger" not in resp.headers  # no error
        row.refresh_from_db()
        assert row.is_primary is True
        spy.assert_not_called()  # step-up skipped for the bootstrap

    @pytest.mark.django_db
    def test_enable_login_bootstraps_without_step_up(self, mocker):
        spy = mocker.patch("core.views_connected_addresses.verify_step_up")
        u = user_with_address(ALGO_A)
        row = linked(u.profile, ALGO_A, login=False)
        resp = self._action(
            u, {"operation": "set_login", "target_id": row.id, "enabled": "true"}
        )
        assert "HX-Trigger" not in resp.headers
        row.refresh_from_db()
        assert row.login_enabled is True
        spy.assert_not_called()

    @pytest.mark.django_db
    def test_non_matching_address_still_requires_step_up(self, mocker):
        spy = mocker.patch(
            "core.views_connected_addresses.verify_step_up",
            return_value="Step-up required",
        )
        u = user_with_address(ALGO_A)
        row = linked(u.profile, ALGO_B)  # different from profile.address
        resp = self._action(u, {"operation": "set_primary", "target_id": row.id})
        assert (
            json.loads(resp.headers["HX-Trigger"])["wallet-error"] == "Step-up required"
        )
        row.refresh_from_db()
        assert row.is_primary is False
        spy.assert_called_once()
