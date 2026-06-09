"""Functional tests for the server-rendered address and bundle pages."""

import json
import os
from unittest import mock

from .base import FunctionalTest

SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "utils",
    "tests",
    "sample_serialized_540A5.json",
)

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
ADDRESS2 = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
BUNDLE = "540A5D8CEC896E073F9170AF0A962503E69147CF"


def _sample_payload():
    with open(SAMPLE_PATH) as sample_file:
        return json.load(sample_file)


class AddressPageTest(FunctionalTest):
    """Render the single-address page from a mocked backend payload."""

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_address_page_components(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}

        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.accept_cookie()

        self.assertTrue(self.browser.current_url.rstrip("/").endswith(ADDRESS))
        self.assertIn(ADDRESS, self.browser.page_source)
        self.assertTrue(self.find_elems_by_class("consolidated"))
        # Single address: the value is forwarded as-is (no separate address list).
        mocked_fetch.assert_called_once_with(ADDRESS, ADDRESS)


class BundlePageTest(FunctionalTest):
    """Render the multi-address bundle page from a mocked backend payload."""

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.check_forbidden_addresses")
    @mock.patch("core.views.check_bundle_addresses")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_bundle_page_passes_resolved_addresses(
        self,
        mocked_fetch,
        mocked_check_bundle,
        mocked_forbidden,
        mocked_status,
        mocked_capabilities,
    ):
        addresses = f"{ADDRESS} {ADDRESS2}"
        mocked_fetch.return_value = _sample_payload()
        mocked_check_bundle.return_value = addresses
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}

        self.browser.get(f"{self.server_url}/{BUNDLE}")
        self.accept_cookie()

        self.assertTrue(self.find_elems_by_class("consolidated"))
        # Validates the core/views.py fix: the resolved address list — not just
        # the opaque hash — is forwarded to the backend client, so a multi-address
        # bundle resolves server-side.
        mocked_fetch.assert_called_once_with(BUNDLE, addresses)
