"""Testing module for :py:mod:`walletauth.gating_views` module."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from walletauth.gating_views import SwapGateAPIView
from walletauth.models import LinkedAddress

user_model = get_user_model()

ALGO = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


def make_user(username="owner"):
    return user_model.objects.create(username=username)


def link(profile, address):
    LinkedAddress.objects.create(
        profile=profile,
        address=address,
        canonical_address=address,
        chain="algorand",
        auth_method="algorand_wallet",
        is_primary=True,
        login_enabled=True,
    )


def post(data, user=None):
    request = APIRequestFactory().post("/gate/", data, format="json")
    if user is not None:
        force_authenticate(request, user=user)
    return SwapGateAPIView.as_view()(request)


class TestSwapGateAPIView:
    """Testing class for :class:`SwapGateAPIView`."""

    @pytest.mark.django_db
    def test_returns_connected_subset(self):
        user = make_user()
        link(user.profile, ALGO)
        response = post({"addresses": [ALGO, "OTHERADDR"]}, user)
        assert response.status_code == 200
        assert response.data["linked"] == [ALGO]

    @pytest.mark.django_db
    def test_accepts_single_address(self):
        user = make_user()
        link(user.profile, ALGO)
        response = post({"address": ALGO}, user)
        assert response.status_code == 200
        assert response.data["linked"] == [ALGO]

    @pytest.mark.django_db
    def test_anonymous_gets_empty(self):
        response = post({"addresses": [ALGO]})
        assert response.status_code == 200
        assert response.data["linked"] == []

    @pytest.mark.django_db
    def test_self_scoped_no_oracle_for_other_accounts(self):
        owner = make_user("owner")
        link(owner.profile, ALGO)
        snooper = make_user("snooper")
        response = post({"addresses": [ALGO]}, snooper)
        assert response.status_code == 200
        assert response.data["linked"] == []

    @pytest.mark.django_db
    def test_missing_addresses_returns_empty(self):
        user = make_user()
        response = post({}, user)
        assert response.status_code == 200
        assert response.data["linked"] == []

    @pytest.mark.django_db
    def test_non_list_addresses_rejected(self):
        user = make_user()
        response = post({"addresses": "notalist"}, user)
        assert response.status_code == 400
