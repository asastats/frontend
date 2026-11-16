from django.urls import reverse

from .base import FunctionalTest


class VestigeApiDocsTest(FunctionalTest):
    """The Vestige-compatible prices in the API's two documentation pages."""

    def test_swagger_ui_shows_the_vestige_compatible_prices(self):
        # Urlike builds a wallet that asked Vestige for prices; she opens the API docs
        self.browser.get(self.server_url + reverse("swagger-ui"))

        # She finds a section for the endpoints kept compatible with Vestige
        self.wait_until(
            lambda: "Vestige compatibility" in self.find_elem_by_id("swagger-ui").text,
            timeout=20,
        )

        # And in it the path she already calls
        self.assertIn(
            "/api/vestige/assets/price", self.find_elem_by_id("swagger-ui").text
        )

    def test_redoc_shows_the_vestige_compatible_prices(self):
        # Urlike prefers the other documentation page
        self.browser.get(self.server_url + reverse("redoc"))

        # She finds the same section, and how to move over from Vestige
        self.wait_until(
            lambda: "Moving from Vestige" in self.find_elem_by_tag("body").text,
            timeout=20,
        )
        self.assertIn("Vestige compatibility", self.find_elem_by_tag("body").text)
