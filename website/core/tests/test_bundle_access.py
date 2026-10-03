"""Testing who may view a bundle larger than anyone can type."""

import time

import pytest
from algosdk import account
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages import get_messages
from django.http import Http404, HttpResponse
from django.urls import reverse

from core.helpers import may_view_bundle
from core.models import BundleName
from core.views import NftCollectionItemsView
from utils.constants.core import MAX_BUNDLE_SIZE
from utils.constants.users import BUNDLE_NOT_VIEWABLE_ERROR
from utils.helpers import bundle_from_addresses

user_model = get_user_model()

LARGE = " ".join(account.generate_account()[1] for _ in range(MAX_BUNDLE_SIZE + 2))
SMALL = " ".join(LARGE.split()[:MAX_BUNDLE_SIZE])


def _user(**kwargs):
    name = f"user{time.time_ns()}"
    return user_model.objects.create(email=f"{name}@testuser.com", username=name, **kwargs)


def _name(user, public=False):
    return BundleName.objects.create(
        profile=user.profile,
        name=f"name-{time.time_ns()}",
        addresses=LARGE,
        public=public,
    )


@pytest.mark.django_db
class TestMayViewBundle:
    def test_anyone_may_view_what_anyone_can_type(self):
        assert may_view_bundle(AnonymousUser(), SMALL)

    def test_a_logged_out_reader_may_not_view_a_private_large_bundle(self):
        _name(_user())

        assert not may_view_bundle(AnonymousUser(), LARGE)

    def test_its_owner_may(self):
        owner = _user()
        _name(owner)

        assert may_view_bundle(owner, LARGE)

    def test_another_subscriber_may_not(self):
        _name(_user())

        assert not may_view_bundle(_user(), LARGE)

    def test_anyone_may_once_a_public_name_points_at_it(self):
        _name(_user(), public=True)

        assert may_view_bundle(AnonymousUser(), LARGE)

    def test_staff_may(self):
        assert may_view_bundle(_user(is_staff=True), LARGE)

    def test_an_unnamed_large_bundle_opens_for_nobody(self):
        assert not may_view_bundle(_user(), LARGE)


@pytest.mark.django_db
class TestBundleViewsRefuse:
    @pytest.fixture(autouse=True)
    def _resolves(self, mocker):
        mocker.patch("core.views.check_bundle_addresses", return_value=LARGE)

    def test_the_address_page_sends_the_reader_to_the_index_told_why(self, client):
        response = client.get(reverse("bundle", args=[bundle_from_addresses(LARGE)]))

        assert response.status_code == 302
        assert response.url == reverse("index")
        assert [str(message) for message in get_messages(response.wsgi_request)] == [
            BUNDLE_NOT_VIEWABLE_ERROR.format(MAX_BUNDLE_SIZE)
        ]

    def test_the_export_page_refuses_too(self, client):
        client.force_login(_user())

        response = client.get(
            reverse("export_bundle", args=[bundle_from_addresses(LARGE)])
        )

        assert response.status_code == 302
        assert response.url == reverse("index")

    def test_the_nft_collection_fragment_is_a_404(self, rf, mocker):
        request = rf.get("/fragment", {"name": "x"})
        request.user = AnonymousUser()
        view = NftCollectionItemsView()
        view.setup(request, bundle_from_addresses(LARGE))
        with pytest.raises(Http404):
            view.get_context_data()

    def test_the_owner_still_reaches_the_address_page(self, client, mocker):
        owner = _user()
        _name(owner)
        client.force_login(owner)
        mocker.patch(
            "core.views.cache_page",
            return_value=lambda view: lambda *args, **kwargs: HttpResponse(b"page"),
        )

        response = client.get(reverse("bundle", args=[bundle_from_addresses(LARGE)]))

        assert response.content == b"page"
