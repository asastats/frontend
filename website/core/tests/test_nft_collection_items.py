"""Testing module for :py:class:`core.views.NftCollectionItemsView`.

The half of the light payload that gives a reader back what the page stopped
sending: an opened collection's listings and purchase history. The page renders
every item already - identity, image, price, traits - so this replaces those
with the same items carrying the parts only an opened card shows.
"""


import pytest
from django.http import Http404
from django.template.loader import render_to_string

from api.client import BackendError
from core.views import NFT_ITEM_TEMPLATES, NftCollectionItemsView

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
BUNDLE = "A" * 40


def _view(mocker, name="Goannas", value=ADDRESS, user=None):
    view = NftCollectionItemsView()
    view.args = (value,)
    view.kwargs = {}
    view.request = mocker.MagicMock()
    view.request.GET = {} if name is None else {"name": name}
    view.request.user = user or mocker.MagicMock(is_authenticated=False)
    return view


class TestNftCollectionItemsView:
    """What the view asks the engine, and what it does when it cannot."""

    def test_it_fetches_the_named_collection(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocked = mocker.patch("core.views.fetch_collection_items")

        context = _view(mocker).get_context_data()

        mocked.assert_called_once_with(ADDRESS, "Goannas", ADDRESS)
        assert context["coll"] is mocked.return_value

    def test_it_resolves_a_bundle_to_its_addresses(self, mocker):
        """A bundle hash means nothing to the engine without them."""
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.check_bundle_addresses", return_value="ONE TWO")
        mocked = mocker.patch("core.views.fetch_collection_items")

        _view(mocker, value=BUNDLE).get_context_data()

        assert mocked.call_args[0][2] == "ONE TWO"

    def test_it_sends_an_empty_name_rather_than_dropping_it(self, mocker):
        """The NFTs belonging to no collection are a collection the page renders
        like any other, and the engine tells an absent `name` from an empty one."""
        mocker.patch("core.views.check_forbidden_addresses")
        mocked = mocker.patch("core.views.fetch_collection_items")

        _view(mocker, name="").get_context_data()

        assert mocked.call_args[0][1] == ""

    def test_a_missing_name_is_a_404(self, mocker):
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.fetch_collection_items")

        with pytest.raises(Http404):
            _view(mocker, name=None).get_context_data()

    def test_it_checks_forbidden_addresses(self, mocker):
        """The same gate the address page applies; this reaches the same data."""
        mocked = mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.fetch_collection_items")

        _view(mocker).get_context_data()

        mocked.assert_called_once_with(ADDRESS)

    def test_a_backend_failure_leaves_no_collection(self, mocker):
        """**Not an exception.** A reader who opened a collection and got a 500
        should see that the details are missing, not a page-wide error."""
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch(
            "core.views.fetch_collection_items",
            side_effect=BackendError("502: upstream"),
        )

        context = _view(mocker).get_context_data()

        assert context["coll"] is None

    @pytest.mark.parametrize("layout", sorted(NFT_ITEM_TEMPLATES))
    def test_it_picks_the_layout_s_item_template(self, mocker, layout):
        mocker.patch("core.views.check_forbidden_addresses")
        mocker.patch("core.views.fetch_collection_items")
        mocker.patch("core.views.layout_for_user", return_value=layout)

        context = _view(mocker).get_context_data()

        assert context["item_template"] == NFT_ITEM_TEMPLATES[layout]

    def test_every_layout_has_an_item_template(self):
        """A layout missing from the table is a KeyError on expand, for the
        readers using it and nobody else."""
        from utils.constants.core import ADDRESS_LAYOUTS

        assert set(NFT_ITEM_TEMPLATES) == set(ADDRESS_LAYOUTS)


class TestNftCollectionItemsPartial:
    """What the swapped-in markup says."""

    def _item(self):
        return {
            "price": "10.0",
            "amount": 1,
            "nft": {
                "id": 505,
                "name": "Goanna #1",
                "urls": [],
                "floor": [{"price": "2.5", "market": {"name": "Asalytic"}}],
            },
        }

    def test_it_renders_one_block_per_item(self):
        html = render_to_string(
            "_nft_collection_items.html",
            {
                "coll": {"nfts": [self._item(), self._item()]},
                "item_template": NFT_ITEM_TEMPLATES["classic"],
            },
        )
        assert html.count('id="505"') == 2

    def test_it_says_so_when_the_fetch_failed(self):
        html = render_to_string(
            "_nft_collection_items.html",
            {"coll": None, "item_template": NFT_ITEM_TEMPLATES["classic"]},
        )
        assert "could not be loaded" in html

    def test_it_distinguishes_an_empty_collection_from_a_failure(self):
        """Both render nothing; only one of them is the reader's fault to retry."""
        html = render_to_string(
            "_nft_collection_items.html",
            {"coll": {"nfts": []}, "item_template": NFT_ITEM_TEMPLATES["classic"]},
        )
        assert "holds no items" in html
        assert "could not be loaded" not in html

    @pytest.mark.parametrize("layout", sorted(NFT_ITEM_TEMPLATES))
    def test_every_layout_s_template_renders(self, layout):
        """The full records the engine returns carry listings and purchases,
        which is the shape only this path renders."""
        item = self._item()
        item["nft"]["listings"] = [
            {"price": "9.0", "market": {"name": "Rand"}, "link": "https://x"}
        ]
        item["nft"]["last_purchase"] = {
            "price": "7.0",
            "epoch": 1725000000,
            "market": {"name": "Rand"},
            "link": "https://y",
        }
        html = render_to_string(
            "_nft_collection_items.html",
            {"coll": {"nfts": [item]}, "item_template": NFT_ITEM_TEMPLATES[layout]},
        )
        assert "Rand" in html
