"""Functional tests for the server-rendered address and bundle pages."""

import json
import os
from unittest import mock

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

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

        self.assertTrue(self.find_elems_by_class("consolidated"))
        # Validates the core/views.py fix: the resolved address list — not just
        # the opaque hash — is forwarded to the backend client, so a multi-address
        # bundle resolves server-side.
        mocked_fetch.assert_called_once_with(BUNDLE, addresses)


class AssetRowLayoutTest(FunctionalTest):
    """What the rows look like, measured in a browser.

    Both defects here were invisible to every other kind of test: the markup
    was correct, the stylesheet contained the rules, and only the rendered
    geometry was wrong.
    """

    def _render(self):
        self.browser.get(f"{self.server_url}/{ADDRESS}")

    def _computed(self, element, prop):
        return self.browser.execute_script(
            "return getComputedStyle(arguments[0])[arguments[1]];", element, prop
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_asset_rows_show_their_chart_colour(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The stripe ties a row to its slice of the pie chart above it.

        Its width was declared on a Materialize class the markup stopped
        emitting, so the colour rules painted a border that was not there. The
        page looked fine; the link between the chart and the list was gone.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._render()

        rows = self.browser.find_elements(By.CSS_SELECTOR, ".token.item-header")
        self.assertTrue(rows, "the page rendered no asset rows")

        widths = {self._computed(row, "borderLeftWidth") for row in rows}
        self.assertEqual(widths, {"4px"}, f"stripe widths: {widths}")

        coloured = [
            row
            for row in rows
            if "c" in (row.get_attribute("class") or "")
        ]
        self.assertTrue(coloured, "no row carries a colour slot")
        greys = {self._computed(row, "borderLeftColor") for row in coloured}
        self.assertNotEqual(
            greys, {"rgb(171, 171, 171)"}, "every stripe fell back to the default grey"
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_collection_thumbnails_share_the_row_with_amount_and_value(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Three columns, not two storeys.

        The conversion put the thumbnails on a line of their own beneath the
        label and the value, which doubled the height of every collection in a
        long list. They belong between the two, wrapping within their own
        column when there are too many to fit.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._render()

        rows = self.browser.find_elements(By.CSS_SELECTOR, ".nft.item-header")
        self.assertTrue(rows, "the page rendered no collection rows")

        for row in rows:
            left = row.find_element(By.CSS_SELECTOR, ".nftleft")
            middle = row.find_element(By.CSS_SELECTOR, ".nftmid")
            right = row.find_element(By.CSS_SELECTOR, ".nftright")
            with self.subTest(collection=left.text[:30]):
                # Left to right on one row: each column starts after the one
                # before it ends, which is false the moment one wraps below.
                self.assertLess(
                    left.location["x"] + left.size["width"],
                    right.location["x"] + right.size["width"],
                )
                self.assertGreaterEqual(
                    middle.location["x"], left.location["x"] + left.size["width"] - 1
                )
                self.assertGreaterEqual(
                    right.location["x"],
                    middle.location["x"] + middle.size["width"] - 1,
                )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_stripe_follows_the_corner_on_every_radius(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Themes disagree about how round a box is, and the stripe must agree.

        `--radius-box` runs from 0rem to 1.125rem across the 57 themes, so a
        stripe drawn to one radius would overshoot the curve on most of them.
        It is clipped to the container's own computed radius instead, which
        resolves per theme -- square on `black`, fully curved on `garden`,
        without either being written down here.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._render()

        seen = {}
        for theme in ("black", "corporate", "garden", "asastats"):
            with self.subTest(theme=theme):
                self.browser.execute_script(
                    "document.documentElement.setAttribute('data-theme', arguments[0]);",
                    theme,
                )
                row = self.browser.find_element(By.CSS_SELECTOR, "details.fitem")

                self.assertEqual(
                    self._computed(row, "overflow"),
                    "hidden",
                    "the container does not clip, so the stripe cannot follow it",
                )
                radius = self._computed(row, "borderTopLeftRadius")
                seen[theme] = radius
                # The stripe is still the full 4px whatever the corner does.
                summary = row.find_element(By.CSS_SELECTOR, ".item-header")
                self.assertEqual(self._computed(summary, "borderLeftWidth"), "4px")

        self.assertGreater(
            len(set(seen.values())),
            1,
            f"every theme reported the same radius, so nothing was proven: {seen}",
        )
        self.assertEqual(seen["black"], "0px", f"black is a square theme: {seen}")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_asset_and_collection_rows_are_the_same_height(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A collection holding one NFT must not tower over an asset row.

        Both sections list one holding per row and should scan as one list.
        They diverged because the conversion sized thumbnails at 3rem while
        asset icons stayed at 2rem, so a single-thumbnail collection was half
        again as tall as the asset beside it. The old design had both at 32px.

        Compared against the *shortest* collection row, since a collection with
        many thumbnails is legitimately taller -- that is the wrapping working.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._render()

        assets = [
            row.size["height"]
            for row in self.browser.find_elements(By.CSS_SELECTOR, ".token.item-header")
        ]
        collections = [
            row.size["height"]
            for row in self.browser.find_elements(By.CSS_SELECTOR, ".nft.item-header")
        ]
        self.assertTrue(assets and collections, "the page rendered no rows to compare")

        self.assertEqual(
            len(set(assets)), 1, f"asset rows are uneven among themselves: {set(assets)}"
        )
        self.assertEqual(
            min(collections),
            assets[0],
            f"shortest collection {min(collections)} vs asset {assets[0]}",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_asset_icon_sits_in_the_middle_of_its_row(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Where the old design had it, and where the thumbnails are.

        The conversion made it the first item in a flex row, so it sat hard
        left against the amount -- the two sections stopped lining up with each
        other.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._render()

        for row in self.browser.find_elements(By.CSS_SELECTOR, ".token.item-header"):
            icon = row.find_element(By.CSS_SELECTOR, ".icondiv")
            with self.subTest(row=row.text[:24]):
                row_centre = row.location["x"] + row.size["width"] / 2
                icon_centre = icon.location["x"] + icon.size["width"] / 2
                self.assertLess(
                    abs(row_centre - icon_centre),
                    2,
                    f"icon centre {icon_centre} vs row centre {row_centre}",
                )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_hovering_a_thumbnail_opens_the_preview_beside_it(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Measured, because the element existed all along.

        The handler ran and appended a div; nothing styled it, so it was
        `position: static` and the coordinates it wrote were ignored. The
        preview ended up at the foot of the document at full size. Only its
        geometry shows the difference.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._render()

        thumbnail = self.browser.find_elements(By.CSS_SELECTOR, ".nfticon")
        if not thumbnail:
            self.skipTest("the sample payload holds no NFTs to hover")
        thumbnail = thumbnail[0]

        ActionChains(self.browser).move_to_element(thumbnail).perform()
        self.wait_until(
            lambda: self.browser.find_elements(By.ID, "id-nft-preview")
        )
        preview = self.browser.find_element(By.ID, "id-nft-preview")

        self.assertEqual(self._computed(preview, "position"), "absolute")
        self.assertEqual(self._computed(preview, "pointerEvents"), "none")
        # Beside the thumbnail it belongs to, not at the end of the page.
        self.assertLess(
            abs(preview.location["y"] - thumbnail.location["y"]),
            400,
            "the preview opened nowhere near the thumbnail",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_filtering_keeps_each_heading_with_its_section(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The headings sit inside the containers the filter hides.

        `address.js` hides every `.section-list` and then reveals only those
        holding a match, so a heading placed outside one would stay on screen
        labelling a section that is no longer there -- and a heading placed
        inside a row's wrapper would vanish while its own rows remained.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._render()

        headings = self.browser.find_elements(By.CSS_SELECTOR, ".section-list h2")
        self.assertTrue(headings, "the lists render no headings")
        self.assertTrue(
            all(h.is_displayed() for h in headings), "a heading starts hidden"
        )

        # Filter to something no asset matches: the sections go, headings with
        # them, and nothing is left labelling an empty page.
        field = self.browser.find_element(By.ID, "filter")
        field.send_keys("zzzznomatch")
        field.send_keys(Keys.ENTER)

        self.wait_until(
            lambda: not any(
                section.is_displayed()
                for section in self.browser.find_elements(
                    By.CSS_SELECTOR, ".asasec, .nftsec"
                )
            )
        )
        self.assertFalse(
            any(h.is_displayed() for h in headings),
            "a heading outlived the section it belongs to",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_charts_stack_their_legend_on_a_narrow_screen(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A quarter-width legend on a phone is a column of single words.

        Below the breakpoint the legend sits above its canvas and takes the
        full width; above it, the two sit side by side.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}

        self.browser.set_window_size(420, 900)
        self._render()
        legend = self.browser.find_element(By.ID, "id-legend-asachart")
        canvas = legend.find_element(By.XPATH, "../div[@class='canvas']")

        self.assertLess(
            legend.location["y"],
            canvas.location["y"],
            "the legend should sit above the canvas when stacked",
        )

        self.browser.set_window_size(1400, 1000)
        self._render()
        legend = self.browser.find_element(By.ID, "id-legend-asachart")
        canvas = legend.find_element(By.XPATH, "../div[@class='canvas']")

        self.assertLess(
            legend.location["x"],
            canvas.location["x"],
            "the legend should sit beside the canvas when there is room",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_charts_never_overflow_their_column(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Every canvas carries `width="500"`, which is wider than a phone.

        `min-width: 0` is what lets a flex item shrink below its content;
        without it the canvas pushes the page sideways and the whole address
        page scrolls horizontally.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}

        for width in (390, 768, 1400):
            self.browser.set_window_size(width, 900)
            self._render()
            with self.subTest(width=width):
                self.assertLessEqual(
                    self.browser.execute_script(
                        "return document.documentElement.scrollWidth;"
                    ),
                    self.browser.execute_script("return window.innerWidth;") + 1,
                    "the page scrolls sideways",
                )
