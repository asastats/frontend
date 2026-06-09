"""Integration tests for :py:mod:`asastats.core.views` module."""

import pytest
from django.test import TestCase

TEST_ADDRESS = "TIIHS4257NZIQCQEYKI3WHCKACXDA37FP42JLJEZ7R5MXGQS63KFS7PR34"


class AddressPageTest(TestCase):
    # @pytest.mark.skip()
    def test_address_page_renders_address_template(self):
        response = self.client.get(f"/{TEST_ADDRESS}")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "address.html")


class TokenomicsPageTest(TestCase):
    # @pytest.mark.skip()
    def test_tokenomics_page_renders_tokenomics_template(self):
        response = self.client.get("/tokenomics/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tokenomics.html")
