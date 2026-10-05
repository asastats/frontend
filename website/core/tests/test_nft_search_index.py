"""Testing module for :py:class:`core.views.NftSearchIndexView`.

The text of NFTs the page did not render, for the dynamic toolbar's "All
collections" search on an account past ``ADDRESS_DEFER_ITEMS_ABOVE_COLLECTIONS``.
"""

import json

import pytest
from django.conf import settings
from django.http import Http404
from django.template.loader import render_to_string

from api.client import BackendError
from core.views import NftSearchIndexView, nft_search_index

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
BUNDLE = "A" * 40


def _collection(name, *nfts):
    return {"name": name, "nfts": [{"nft": nft} for nft in nfts]}


def _request(mocker, user=None):
    request = mocker.MagicMock()
    request.user = user or mocker.MagicMock(is_authenticated=False, profile=None)
    return request


class TestNftSearchIndex:
    """The index itself: what goes in, and under which key."""

    def test_it_keys_each_collection_by_its_card_id(self):
        index = nft_search_index(
            [
                _collection(
                    "Brave New World",
                    {"id": 101, "name": "Brave #1", "unit": "BRV1", "title": "First"},
                )
            ]
        )

        assert index == {"fbrave-new-world": "brave #1 brv1 first 101"}

    def test_it_skips_empty_fields_and_missing_records(self):
        index = nft_search_index(
            [_collection("Puffins", {"id": 7, "name": "", "unit": None}, None)]
        )

        assert index == {"fpuffins": "7"}

    def test_a_collection_with_no_name_slugs_as_the_template_does(self):
        """`{{ coll.name|slugify }}` turns None into "none"; the key must agree."""
        rendered = render_to_string(
            "snippets/dynamic/collection.html",
            {"coll": {"name": None, "nfts": []}, "url_value": ADDRESS},
        )

        key = next(iter(nft_search_index([_collection(None)])))

        assert f'id="{key}"' in rendered


class TestNftSearchIndexView:
    """What the view checks, what it asks the engine, and how it fails."""

    def test_it_returns_the_index_of_the_light_payload(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocked = mocker.patch(
            "core.views.fetch_and_serialize_account",
            return_value={
                "nftcollections": [_collection("Goannas", {"id": 1, "name": "G1"})]
            },
        )

        response = NftSearchIndexView().get(_request(mocker), ADDRESS.lower())

        assert response.status_code == 200
        assert json.loads(response.content) == {"fgoannas": "g1 1"}
        mocked.assert_called_once_with(ADDRESS, ADDRESS, light=True, permission=0)

    def test_it_resolves_a_bundle_to_its_addresses(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.check_bundle_addresses", return_value="ONE TWO")
        mocker.patch("core.views.may_view_bundle", return_value=True)
        mocked = mocker.patch("core.views.fetch_and_serialize_account", return_value={})

        NftSearchIndexView().get(_request(mocker), BUNDLE)

        assert mocked.call_args[0][1] == "ONE TWO"

    def test_it_passes_the_readers_permission(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocked = mocker.patch("core.views.fetch_and_serialize_account", return_value={})
        user = mocker.MagicMock(is_authenticated=True)
        user.profile.permission = 9

        NftSearchIndexView().get(_request(mocker, user), ADDRESS)

        assert mocked.call_args.kwargs["permission"] == 9

    def test_it_checks_forbidden_addresses(self, mocker):
        mocked = mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.fetch_and_serialize_account", return_value={})

        NftSearchIndexView().get(_request(mocker), ADDRESS)

        mocked.assert_called_once_with(ADDRESS)

    def test_a_bundle_the_reader_may_not_view_is_a_404(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.check_bundle_addresses", return_value="ONE TWO")
        mocker.patch("core.views.may_view_bundle", return_value=False)
        mocked = mocker.patch("core.views.fetch_and_serialize_account")

        with pytest.raises(Http404):
            NftSearchIndexView().get(_request(mocker), BUNDLE)
        mocked.assert_not_called()

    def test_a_backend_failure_is_an_empty_503(self, mocker):
        """The button says it could not load and lets the reader try again."""
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch(
            "core.views.fetch_and_serialize_account", side_effect=BackendError("down")
        )

        response = NftSearchIndexView().get(_request(mocker), ADDRESS)

        assert response.status_code == 503
        assert json.loads(response.content) == {}


class TestAllCollectionsButton:
    """`#tb-allnft` renders only where items are left to the fetch-on-open."""

    def _toolbar(self, count):
        account = {"nftcollections": [_collection(f"C{i}") for i in range(count)]}
        return render_to_string(
            "snippets/dynamic/toolbar.html", {"account": account, "url_value": ADDRESS}
        )

    def test_past_the_fold_the_button_points_at_the_index(self):
        html = self._toolbar(settings.ADDRESS_DEFER_ITEMS_ABOVE_COLLECTIONS + 1)

        assert 'id="tb-allnft"' in html
        assert f'data-url="/nft-search/{ADDRESS}/"' in html

    def test_at_the_fold_there_is_no_button(self):
        html = self._toolbar(settings.ADDRESS_DEFER_ITEMS_ABOVE_COLLECTIONS)

        assert 'id="tb-allnft"' not in html
