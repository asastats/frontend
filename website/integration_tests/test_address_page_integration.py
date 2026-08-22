"""Integration tests for the address page against the live backend.

The only existing coverage of this page asserted a 200 and the template name,
which is satisfied by a page rendering nothing at all. That is thin for the
most backend-dependent page in the project -- it consumes the whole API 2.0
serialized payload, fans it out across three snippet subtrees, and derives five
chart datasets from it.

It is also the last template still on base.html, so it is next to be converted.
These tests exist to be the before-and-after oracle for that conversion: they
assert that what the backend returned actually reaches the rendered page, so a
redesign that quietly drops a row, a value or a collection fails here rather
than being noticed by a user.

Two choices keep them useful across that rewrite:

* they assert against ``response.context`` where the question is about data,
  which no amount of markup change can affect;
* where the question is genuinely about the rendered page, they anchor on
  ``id="f<asset id>"`` and ``data-val`` -- attributes address.js selects on,
  and which core/tests/test_template_hooks.py already protects. Presentation
  classes are deliberately never asserted, because those are exactly what the
  redesign is entitled to change.

``LIGHT_ADDRESS`` holds enough to be meaningful (11 assets, 2 NFT collections)
while staying inside the read timeout on modest hardware. The heavier
``api.data`` fixtures are used only where breadth genuinely needs them.
"""

from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from api.client import fetch_serialized_account
from api.data import API_EXAMPLE_BUNDLE1
from utils.helpers import check_bundle_addresses

#: A real mainnet address, small enough to evaluate well within the backend
#: read timeout and varied enough to cover assets, NFTs and non-valued items.
LIGHT_ADDRESS = "OGRUNXPSMO7Z7EGOGONA7BVEIN7YIJZZB372GZGJIAPB363C6KB42CEN2M"

#: Keys BaseAddressView documents as its contract with the template.
EXPECTED_CONTEXT_KEYS = [
    "account",
    "asachart",
    "colors",
    "consolidated",
    "distchart",
    "is_bundle",
    "nft_colors",
    "nftchart",
]


class AddressPageDataTest(TestCase):
    """Testing class for payload delivery to the address page."""

    @classmethod
    def setUpClass(cls):
        # One evaluation shared by the class: each is a live backend call, and
        # asserting different facets of the same response is the point.
        #
        # setUpClass rather than setUpTestData, which deep-copies whatever it
        # stores so each test gets an isolated copy -- and a response carries a
        # ResolverMatch, which cannot be pickled. Isolation is not needed here:
        # nothing mutates the response.
        super().setUpClass()
        # The address page is `cache_page`'d, and a *replayed* cached response
        # carries no `templates` and no `context` -- so every assertion below
        # fails with "No templates used" and a `NoneType` subscript if anything
        # rendered this address first. That became real when the money-column
        # integration tests arrived: they render this same address for a free
        # reader, which stores an entry under the very same `layout-classic`
        # prefix. Clearing here forces the miss these tests are written around.
        cache.clear()
        cls.response = Client().get(f"/{LIGHT_ADDRESS}")

    def test_integration_address_page_renders(self):
        """Guard the guard: everything below reads this response."""
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "address.html")

    def test_integration_address_page_publishes_its_documented_context(self):
        """BaseAddressView names these keys in its docstring; keep them real."""
        missing = [
            key for key in EXPECTED_CONTEXT_KEYS if key not in self.response.context
        ]
        self.assertEqual(
            missing,
            [],
            f"the view no longer publishes {missing}. Its docstring lists these "
            "as the contract with address.html, and the snippets bind to them.",
        )

    def test_integration_address_page_carries_a_populated_payload(self):
        """An empty evaluation would satisfy every 200-and-template test."""
        account = self.response.context["account"]

        self.assertEqual(
            account["account_info"]["addresses"],
            [LIGHT_ADDRESS],
            "the page evaluated a different address than the url asked for",
        )
        self.assertFalse(self.response.context["is_bundle"])
        self.assertTrue(
            account["asaitems"],
            "no asset rows came back for an address known to hold assets -- "
            "the page would render as an empty shell and still return 200",
        )
        self.assertTrue(account["nftcollections"], "no NFT collections came back")
        self.assertTrue(float(account["total"]["total"]) > 0, "total evaluates to zero")

    def test_integration_address_page_agrees_with_the_api(self):
        """The page and /api/v2/ must not diverge.

        Both go through ``fetch_serialized_account``, so a difference means
        the page is transforming the payload on its way to the template --
        which is precisely the kind of drift no unit test would catch, because
        both sides would be mocked with the same fixture.
        """
        from_api = fetch_serialized_account(LIGHT_ADDRESS)
        from_page = self.response.context["account"]

        self.assertEqual(
            from_page["account_info"]["addresses"],
            from_api["account_info"]["addresses"],
            "the page and the API resolved different address lists",
        )
        self.assertEqual(
            sorted(item["asset"]["id"] for item in from_page["asaitems"]),
            sorted(item["asset"]["id"] for item in from_api["asaitems"]),
            "the page and the API disagree about which assets are held",
        )


class AddressPageRenderTest(TestCase):
    """Testing class for payload values reaching the rendered HTML.

    This is the half that a template rewrite can break: the data can be
    perfectly correct in the context and never make it onto the page.
    """

    @classmethod
    def setUpClass(cls):
        # See AddressPageDataTest.setUpClass for why this is not setUpTestData.
        super().setUpClass()
        # The address page is `cache_page`'d, and a *replayed* cached response
        # carries no `templates` and no `context` -- so every assertion below
        # fails with "No templates used" and a `NoneType` subscript if anything
        # rendered this address first. That became real when the money-column
        # integration tests arrived: they render this same address for a free
        # reader, which stores an entry under the very same `layout-classic`
        # prefix. Clearing here forces the miss these tests are written around.
        cache.clear()
        cls.response = Client().get(f"/{LIGHT_ADDRESS}")

    def test_integration_every_asset_row_is_rendered(self):
        """One `id="f<asset id>"` anchor per asaitem, none missing."""
        account = self.response.context["account"]
        html = self.response.content.decode()

        missing = [
            item["asset"]["id"]
            for item in account["asaitems"]
            if f'id="f{item["asset"]["id"]}"' not in html
        ]
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} of {len(account['asaitems'])} asset rows are in "
            f"the context but not on the page: {missing}. address.js selects "
            "these anchors, so losing them breaks the section links as well "
            "as the display.",
        )

    def test_integration_every_asset_value_is_rendered(self):
        """`data-val` must carry the payload's value, unrounded.

        The visible text is rounded for display; `data-val` is what address.js
        reads to recompute totals in USD, so it is the one that has to match
        the payload exactly.
        """
        account = self.response.context["account"]
        html = self.response.content.decode()

        missing = [
            (item["asset"]["unit"], item["value"])
            for item in account["asaitems"]
            if f'data-val="{item["value"]}"' not in html
        ]
        self.assertEqual(
            missing,
            [],
            f"values present in the payload never reached the page: {missing}",
        )

    def test_integration_every_nft_collection_is_rendered(self):
        """NFT collections have their own snippet subtree and their own risk."""
        account = self.response.context["account"]
        html = self.response.content.decode()

        missing = [
            coll["name"]
            for coll in account["nftcollections"]
            if f'data-val="{coll["value"]}"' not in html
        ]
        self.assertEqual(
            missing,
            [],
            f"NFT collections missing from the page: {missing}",
        )

    def test_integration_asset_units_are_rendered(self):
        """The unit is what identifies a row to a reader."""
        account = self.response.context["account"]
        html = self.response.content.decode()

        missing = [
            item["asset"]["unit"]
            for item in account["asaitems"]
            if item["asset"]["unit"] and item["asset"]["unit"] not in html
        ]
        self.assertEqual(missing, [], f"asset units missing from the page: {missing}")


class BundlePageTest(TestCase):
    """Testing class for the bundle branch of the same view.

    A bundle takes a different path through ``dispatch`` -- the url value is a
    40-character hash resolved to an address list -- and sets ``is_bundle``,
    which the template uses to choose between two whole blocks of markup. The
    light address cannot exercise any of that, so one heavier fixture does.
    """

    # The runtime timeout is what a *page load* should tolerate; a cold
    # evaluation of a multi-address bundle legitimately takes longer than a
    # visitor would ever wait for. Raising it here keeps a slow backend from
    # reporting as a broken bundle -- the thing under test is resolution and
    # rendering, not latency.
    @override_settings(ASASTATS_API_TIMEOUT=180)
    def test_integration_bundle_page_resolves_and_renders(self):
        # See AddressPageDataTest.setUpClass: a cached response has no context.
        cache.clear()
        response = self.client.get(f"/{API_EXAMPLE_BUNDLE1}")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address.html")
        self.assertTrue(
            response.context["is_bundle"],
            "a 40-character bundle hash did not set is_bundle, so the page "
            "rendered the single-address branch of the template",
        )
        self.assertEqual(
            response.context["account"]["account_info"]["addresses"],
            check_bundle_addresses(API_EXAMPLE_BUNDLE1).split(" "),
            "the bundle resolved to a different address list than the one "
            "stored for that hash",
        )
