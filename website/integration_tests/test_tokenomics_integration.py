"""Integration tests for the tokenomics page's backend call.

``TokenomicsView`` calls ``fetch_price()`` on every render and degrades the way
the capabilities context processor does::

    except (BackendError, Exception):  # noqa: BLE001 - never break rendering
        context["price"] = None

That guard was added because tokenomics was the only page on the site that
returned a 500 with the engine down. It is the right behaviour, and it has the
same consequence as every other silent fallback: the existing test -- a 200 and
a template name -- passes identically whether a price arrived or not. These
tests are the only place that distinction is made.

A finding worth recording here, because it is the reason these tests assert
against the context rather than the rendered page: **the price is fetched and
never displayed**. ``tokenomics.html`` does not reference ``price``, nor does
``jsonld/tokenomics.jsonld``, and ``git show HEAD:`` confirms it did not before
the redesign either. So every render of this page makes a live HTTP call to the
backend whose result is discarded.

That is left as it stands, deliberately -- deciding between "render it" and
"stop fetching it" is a product call, not a testing one. What these tests fix
is that the call is currently unobserved: if the price endpoint broke, nothing
anywhere would notice.
"""

from django.test import TestCase

from api.client import fetch_price


class PriceEndpointTest(TestCase):
    """Testing class for the /api/v2/price/ contract."""

    def test_integration_price_endpoint_answers(self):
        """The backend must serve a price at all."""
        price = fetch_price()

        self.assertIsNotNone(
            price,
            "the price endpoint returned nothing. The view swallows this and "
            "publishes None, so no page would look broken.",
        )

    def test_integration_price_is_a_usable_number(self):
        """A string, a dict or a zero would all satisfy "is not None"."""
        price = fetch_price()

        self.assertIsInstance(
            price,
            (int, float),
            f"price came back as {type(price).__name__} ({price!r}); anything "
            "rendering or computing with it would need to guess at the type",
        )
        self.assertGreater(
            price,
            0,
            f"price is {price}, which cannot be a real ALGO price and would "
            "render as a broken figure if the page ever displayed it",
        )


class TokenomicsPageTest(TestCase):
    """Testing class for what the tokenomics page receives and renders."""

    def setUp(self):
        self.response = self.client.get("/tokenomics/")

    def test_integration_tokenomics_page_renders(self):
        """Guard the guard: the rest of the class reads this response."""
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "tokenomics.html")

    def test_integration_tokenomics_page_is_not_serving_the_degraded_price(self):
        """The distinction the existing 200-and-template test cannot make.

        ``None`` here is exactly what the ``except`` branch publishes, so it
        means the backend call failed and was swallowed -- indistinguishable
        from success on the page itself, which is why it is asserted here.
        """
        self.assertIsNotNone(
            self.response.context["price"],
            "the view published price=None, which is its failure value. The "
            "page still returned 200 and used its template, so no other test "
            "in the suite can tell that the backend call did not work.",
        )

    def test_integration_tokenomics_page_publishes_a_usable_price(self):
        """What reaches the template must be the same shape the endpoint gave."""
        price = self.response.context["price"]

        self.assertIsInstance(price, (int, float), f"price is {price!r}")
        self.assertGreater(price, 0, f"price is {price}")

    def test_integration_tokenomics_page_renders_its_transparency_reports(self):
        """Every report the loader found must reach the page as a link.

        ``load_transparency_reports()`` scans ``STATIC_ROOT/assets`` rather
        than the backend, and the PDFs it looks for are deployment assets that
        a working checkout need not have. So the assertion is conditional on
        the data existing: with reports present it is a real check that the
        loader's output is rendered, and with none present it skips loudly
        rather than passing on an empty list -- which would be a test that can
        never fail.
        """
        reports = self.response.context["transparency_reports"]
        if not reports:
            self.skipTest(
                "no transparency report PDFs under STATIC_ROOT/assets, so "
                "there is nothing for the page to render. They are deployment "
                "assets; run collectstatic where they exist to exercise this."
            )

        missing = [
            f"{report['year']}-{report['month']}"
            for report in reports
            if f"transparency-report-{report['year']}-{report['month']}.pdf"
            not in self.response.content.decode()
        ]
        self.assertEqual(
            missing,
            [],
            f"reports present in the context never reached the page: {missing}",
        )
