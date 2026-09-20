"""Conditional GET on the address API.

What this is for is recorded in `post-deploy/ANALYSIS-bandwidth-lever.md`: it
bounds the caller polling faster than blocks. It is **not** a compression
scheme, and a block-rate poller still gets a body most blocks.
"""

from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from api.data import API_EXAMPLE_BUNDLE1
from api.views import BaseAddressView, _etag_for
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

pytestmark = pytest.mark.django_db


class TestApiViewsEtagFor:
    """Testing class for :py:func:`api.views._etag_for`."""

    def test_api_views_etag_is_stable_for_equal_data(self):
        """**An ETag that varied with worker identity would never match.**

        A dict iterating in a different order between processes is the same
        answer, so the hash is taken over sorted keys.
        """
        first = {"total": {"total": 1.0}, "asaitems": [{"id": 1}, {"id": 2}]}
        second = {"asaitems": [{"id": 1}, {"id": 2}], "total": {"total": 1.0}}

        assert _etag_for(first) == _etag_for(second)

    def test_api_views_etag_changes_when_a_figure_moves(self):
        """The whole point: a re-priced page must not answer 304."""
        before = {"total": {"total": 1.0}}
        after = {"total": {"total": 1.000001}}

        assert _etag_for(before) != _etag_for(after)

    def test_api_views_etag_survives_decimals(self):
        """The payload carries Decimals, which plain json refuses."""
        assert _etag_for({"total": Decimal("1.5")})

    def test_api_views_etag_is_empty_when_it_cannot_be_computed(self, mocker):
        """**A body we cannot hash is one we offer no ETag for.**

        The caller then gets the full response every time, which is what
        happens today - a degradation to the previous behaviour rather than an
        error.
        """
        mocker.patch("api.views.json.dumps", side_effect=TypeError("nope"))
        logged = mocker.patch("api.views.logger")

        assert _etag_for({"total": 1}) == ""
        assert logged.warning.called

    def test_api_views_etag_is_quoted(self):
        """RFC 9110 wants an entity-tag in quotes; an unquoted one is not a
        valid ETag and clients may refuse to echo it."""
        etag = _etag_for({"total": 1})

        assert etag.startswith('"') and etag.endswith('"')


class TestApiViewsConditionalGet:
    """The 304 path as a request sees it."""

    def _view(self, mocker, serialized, headers=None, user=None):
        factory = APIRequestFactory()
        request = factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}", headers=headers or {})
        if user is not None:
            request.user = user
        view = BaseAddressView()
        view.request = request
        view.args, view.kwargs = (), {}
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        mocker.patch("api.views.fetch_and_serialize_account")
        mocker.patch("api.views.processed_account", return_value=serialized)
        mocker.patch("api.views.live.subscribe", return_value=False)
        return view, request

    def test_api_views_sends_an_etag_on_a_normal_response(self, mocker):
        view, request = self._view(mocker, {"total": {"total": 1.0}})

        response = view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert response.status_code == status.HTTP_200_OK
        assert response["ETag"] == _etag_for({"total": {"total": 1.0}})

    def test_api_views_answers_304_when_the_body_is_unchanged(self, mocker):
        body = {"total": {"total": 1.0}}
        view, request = self._view(
            mocker, body, headers={"If-None-Match": _etag_for(body)}
        )

        response = view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response["ETag"] == _etag_for(body)

    def test_api_views_304_carries_no_body(self, mocker):
        """A 304 with a body is not a saving, it is a protocol violation."""
        body = {"total": {"total": 1.0}}
        view, request = self._view(
            mocker, body, headers={"If-None-Match": _etag_for(body)}
        )

        response = view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert not response.data

    def test_api_views_a_stale_etag_gets_the_full_body(self, mocker):
        """**The case that matters most.** A re-price moves a figure, the ETag
        changes, and the caller must get the new account rather than a 304
        telling them nothing moved."""
        view, request = self._view(
            mocker,
            {"total": {"total": 2.0}},
            headers={"If-None-Match": _etag_for({"total": {"total": 1.0}})},
        )

        response = view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"total": {"total": 2.0}}

    def test_api_views_304_still_reports_the_warm_state(self, mocker):
        """**The conditional caller is exactly who wants to know.**

        Someone polling with `If-None-Match` is the caller most likely to care
        whether their pages are still warm; dropping the header on precisely
        those responses would make it useless to them.
        """
        from django.contrib.auth.models import User

        user = User.objects.create(username="pro2", email="p2@example.com")
        user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
        user.profile.save()
        body = {"total": {"total": 1.0}}
        view, request = self._view(
            mocker, body, headers={"If-None-Match": _etag_for(body)}, user=user
        )

        response = view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert response.status_code == status.HTTP_304_NOT_MODIFIED
        assert response["X-ASAStats-Warm"] == "0"

    def test_api_views_no_etag_header_means_no_conditional_check(self, mocker):
        """The overwhelming majority of callers send nothing and are
        unaffected."""
        view, request = self._view(mocker, {"total": {"total": 1.0}})

        response = view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert response.status_code == status.HTTP_200_OK
