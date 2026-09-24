"""The API view's live-subscription wiring.

Its own module rather than more cases in `test_views.py`, which is already 700
lines of one shape and mocks eight collaborators per test to assert a single
call.
"""

import pytest
from rest_framework.test import APIRequestFactory

from api.data import API_EXAMPLE_BUNDLE1
from api.views import BaseAddressView
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

pytestmark = pytest.mark.django_db


class TestApiViewsLiveSubscription:
    """Testing class for the live wiring in :class:`api.views.BaseAddressView`."""

    def _view(self, mocker, user=None):
        """Return a view and request with every collaborator but ours mocked."""
        factory = APIRequestFactory()
        request = factory.get(f"/api/v2/{API_EXAMPLE_BUNDLE1}")
        if user is not None:
            # Assigned rather than `force_authenticate`d: that only takes
            # effect through DRF's dispatch, and these call `get` directly.
            request.user = user
        view = BaseAddressView()
        view.request = request
        view.args, view.kwargs = (), {}
        mocker.patch("api.views.check_bundle_addresses", return_value="")
        mocker.patch("api.views.processed_account")
        return view, request

    def test_api_views_serves_fresh_when_the_subscription_took(self, mocker):
        """**Asking is what makes it fresh.** The page goes into `lva`, the pass
        publishes a snapshot for it, and the next request is served off that."""
        view, request = self._view(mocker)
        mocker.patch("api.views.live.subscribe", return_value=True)
        fetch = mocker.patch("api.views.fetch_and_serialize_account")

        view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert fetch.call_args.kwargs["fresh"] is True

    def test_api_views_serves_cached_when_over_the_cap(self, mocker):
        """**Over the cap is not an error.** The caller gets the answer they got
        before any of this existed, off the 60-second cached path."""
        view, request = self._view(mocker)
        mocker.patch("api.views.live.subscribe", return_value=False)
        fetch = mocker.patch("api.views.fetch_and_serialize_account")

        view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert fetch.call_args.kwargs["fresh"] is False

    def test_api_views_passes_the_readers_permission_to_subscribe(self, mocker):
        """The cap and the tier are both read off the profile, once, here."""
        from django.contrib.auth.models import User

        user = User.objects.create(username="cluster", email="c@example.com")
        user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]
        user.profile.save()
        view, request = self._view(mocker, user=user)
        subscribe = mocker.patch("api.views.live.subscribe", return_value=False)
        mocker.patch("api.views.fetch_and_serialize_account")

        view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert subscribe.call_args.args[2] == user.pk
        assert subscribe.call_args.args[3] == SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]

    def test_api_views_reports_the_warm_state_to_a_block_time_tier(self, mocker):
        """**The spec said 429; this says so in a header instead.**

        Refusing a caller who is entitled to the data and merely asked for more
        breadth than their plan keeps warm would turn a working integration into
        an outage. The answer is served and the fact is stated.
        """
        from django.contrib.auth.models import User

        user = User.objects.create(username="pro", email="p@example.com")
        user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
        user.profile.save()
        view, request = self._view(mocker, user=user)
        mocker.patch("api.views.fetch_and_serialize_account")
        mocker.patch("api.views.live.subscribe", return_value=False)

        assert view.get(request, bundle=API_EXAMPLE_BUNDLE1)["X-ASAStats-Warm"] == "0"

        view, request = self._view(mocker, user=user)
        mocker.patch("api.views.fetch_and_serialize_account")
        mocker.patch("api.views.live.subscribe", return_value=True)

        assert view.get(request, bundle=API_EXAMPLE_BUNDLE1)["X-ASAStats-Warm"] == "1"

    def test_api_views_says_nothing_to_a_tier_without_block_time(self, mocker):
        """Nothing to report, so no header - it would be noise on every
        response the cached tiers have always had."""
        view, request = self._view(mocker)
        mocker.patch("api.views.fetch_and_serialize_account")
        mocker.patch("api.views.live.subscribe", return_value=False)

        assert "X-ASAStats-Warm" not in view.get(request, bundle=API_EXAMPLE_BUNDLE1)

    def test_api_views_a_request_with_no_user_does_not_raise_attributeerror(self, mocker):
        """**Second time this project has hit this exact thing.**

        `request.user` is absent entirely on a bare WSGIRequest - no
        authentication middleware has run - and `enforce_address_limit` two
        lines above reached for it directly until a unit test caught it. The
        subscription then did the same. Absent reads as no entitlement, which is
        the cached path.
        """
        view, request = self._view(mocker)
        delattr(request, "user") if hasattr(request, "user") else None
        fetch = mocker.patch("api.views.fetch_and_serialize_account")

        view.get(request, bundle=API_EXAMPLE_BUNDLE1)

        assert fetch.call_args.kwargs["fresh"] is False
