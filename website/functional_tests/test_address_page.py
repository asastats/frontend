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


def _unfold(browser, selector=None):
    """Press every load-more control until nothing is folded.

    Both designs reveal one batch per press, so a single click is not "unfold
    this section" any more -- it is "twenty more rows". A test that measures
    geometry needs every row laid out, and a row that is still folded is
    `display: none` with no geometry at all: the measurement reads zero and
    compares it against zero, which passes as often as it fails.

    Bounded rather than looped on the condition. A control that stopped working
    should fail this as a timeout's worth of presses that changed nothing, not
    hang the suite.

    :param browser: the webdriver
    :param selector: a section to unfold, or None for every one on the page
    """
    scope = f"{selector} " if selector else ""
    for _ in range(60):
        remaining = browser.execute_script(
            "var folded = document.querySelectorAll("
            f"  '{scope}[data-folding] > .fitem.folded');"
            "if (!folded.length) return 0;"
            f"document.querySelectorAll('{scope}[data-show-more]')"
            "  .forEach(function (button) { button.click(); });"
            "return folded.length;"
        )
        if not remaining:
            return
    raise AssertionError("the load-more controls never revealed the whole tail")


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
        """Load the page with every section unfolded.

        The load-more rule hides each section's tail past the first
        ``ADDRESS_INITIAL_*`` rows, and a hidden row has no geometry -- every
        measurement in this class would read zero and compare it against zero,
        which passes as often as it fails. Unfolding restores the premise these
        tests were written under: that every row rendered is a row laid out.

        Pressed until nothing is folded rather than once: a press reveals one
        batch now, and this payload carries seventy-six assets against a batch
        of twenty. Clicked rather than styled around, so the control itself is
        exercised on the way to every other assertion here.
        """
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        _unfold(self.browser)
        # Then wait for the images those rows brought with them. `deferImages`
        # assigns every `src` after load, so thumbnails arrive without reserved
        # space and each one that lands pushes the rows below it down. Measuring
        # before they settle compares a coordinate read now against one the page
        # wrote a moment ago, which is a race that reports as a layout bug.
        self.wait_until(
            lambda: self.browser.execute_script(
                "return Array.prototype.every.call("
                "  document.images, function (img) { return img.complete; });"
            )
        )

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


class SectionFoldingTest(FunctionalTest):
    """The load-more rule, measured in a browser.

    Whether a row is *displayed* is the one thing neither the contract tests nor
    jest can answer: the markup carries every row either way, and the difference
    lives entirely in a stylesheet rule keyed off a class on an ancestor.
    """

    def _load(self):
        self.browser.get(f"{self.server_url}/{ADDRESS}")

    def _rows(self, section):
        return self.browser.find_elements(
            By.CSS_SELECTOR, f".{section} [data-folding] > .fitem"
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_tail_of_a_section_starts_hidden(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Hidden, not absent -- the filter still has to be able to find them."""
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._load()

        rows = self._rows("asasec")
        self.assertTrue(rows, "the page rendered no asset rows")
        hidden = [row for row in rows if not row.is_displayed()]

        self.assertTrue(hidden, "nothing was folded away")
        self.assertLess(
            len(hidden),
            len(rows),
            "the whole section was folded, leaving nothing to read",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_control_reveals_one_batch_at_a_time(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A press adds a batch. It used to reveal the whole tail at once.

        Measured on what is *displayed*, which is the one thing neither the
        contract tests nor jest can answer: every row is in the markup either
        way, and the difference lives in a stylesheet rule.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._load()

        button = self.browser.find_element(
            By.CSS_SELECTOR, ".asasec [data-show-more]"
        )
        batch = int(
            self.browser.find_element(By.CSS_SELECTOR, ".asasec").get_attribute(
                "data-initial"
            )
        )
        rows = self._rows("asasec")
        self.assertGreater(
            len(rows), batch * 2, "this payload is too short to fold twice"
        )

        self.assertEqual(len([r for r in rows if r.is_displayed()]), batch)

        self.browser.execute_script("arguments[0].click();", button)
        self.assertEqual(len([r for r in rows if r.is_displayed()]), batch * 2)
        self.assertEqual(button.get_attribute("aria-expanded"), "false")

        self.browser.execute_script("arguments[0].click();", button)
        self.assertEqual(len([r for r in rows if r.is_displayed()]), batch * 3)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_last_batch_turns_the_control_into_its_opposite(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Once everything shows, the only thing left to offer is putting it back."""
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._load()

        button = self.browser.find_element(
            By.CSS_SELECTOR, ".asasec [data-show-more]"
        )
        rows = self._rows("asasec")
        _unfold(self.browser, ".asasec")

        self.assertTrue(
            all(row.is_displayed() for row in rows),
            "a row stayed hidden after every batch was revealed",
        )
        self.assertEqual(button.get_attribute("aria-expanded"), "true")

        self.browser.execute_script("arguments[0].click();", button)
        self.assertTrue(
            any(not row.is_displayed() for row in rows),
            "the section did not fold up again",
        )
        self.assertEqual(button.get_attribute("aria-expanded"), "false")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_control_says_how_many_and_of_what(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """"Show more" tells a reader nothing about whether it is worth a tap.

        And the number it names has to be what the press *does*. It used to be
        the whole tail -- "Show 39 more assets" over a control that revealed
        thirty-nine, which made the label true and the control an unfold. Now it
        names the batch, so this asserts the two agree by pressing it.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._load()

        button = self.browser.find_element(
            By.CSS_SELECTOR, ".asasec [data-show-more]"
        )
        before = len([row for row in self._rows("asasec") if row.is_displayed()])
        promised = int(button.text.split()[1])
        self.assertIn("assets", button.text)

        self.browser.execute_script("arguments[0].click();", button)
        after = len([row for row in self._rows("asasec") if row.is_displayed()])

        self.assertEqual(
            after - before,
            promised,
            f"the control promised {promised} and revealed {after - before}",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_unfolding_one_section_leaves_the_other_folded(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self._load()

        self.browser.execute_script(
            "document.querySelector('.asasec [data-show-more]').click();"
        )

        self.assertTrue(
            any(not row.is_displayed() for row in self._rows("nftsec")),
            "unfolding the assets also unfolded the collections",
        )


class TotalTooltipKeyboardTest(FunctionalTest):
    """The headline figure's tooltip, reached without a pointer.

    It is the only tooltip on this page that carries the exchange rate; every
    other one repeats an amount in the other currency, which the switch already
    gives in one keystroke. So this is the one that has to be reachable, and the
    rest stay pointer conveniences rather than a tab stop per figure.

    Functional rather than markup-only because focusability is a browser fact:
    the attribute can be present and the element still be unreachable if
    something above it takes the focus, and the tooltip's own reveal depends on
    `:focus-visible` matching -- which a rendered-HTML test cannot see.
    """

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_total_takes_focus_and_shows_its_tip(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self.browser.get(f"{self.server_url}/{ADDRESS}")

        total = self.browser.find_element(By.CSS_SELECTOR, ".pricetip")
        wrapper = self.browser.find_element(By.CSS_SELECTOR, ".tooltip[data-tip]")
        hidden = self._tip_opacity(wrapper)
        # Tabbed to, not focused by script. `:focus-visible` is a heuristic the
        # browser applies to how the focus arrived, and a programmatic
        # `.focus()` does not satisfy it -- so a test that called `.focus()`
        # would report the tooltip hidden even when a real reader tabbing to it
        # sees it perfectly well. Pressing Tab is also the thing being claimed.
        self.assertTrue(
            self._tab_to(total),
            "the total is not reachable by tabbing, so its tooltip is "
            "pointer-only",
        )
        # The assertion that matters, and the one this test did not make at
        # first: that focus *reveals* something. DaisyUI keys the reveal on
        # `:has(:focus-visible)` -- a focused descendant -- so a tabindex on the
        # `.tooltip` element itself matches and shows nothing at all. Asserting
        # only that focus landed would have passed against exactly that.
        self.assertEqual(0.0, hidden, "the tip is visible before anything is focused")
        # Waited for, not read straight away: DaisyUI fades the bubble in over
        # 200ms after a 75ms delay, so an immediate read returns the value part
        # way through the transition -- which is 0, and looks exactly like a
        # tooltip that never appeared.
        self.wait_until(lambda: self._tip_opacity(wrapper) == 1.0)

    def _tab_to(self, target, limit=30):
        """Press Tab until `target` has focus. Return whether it ever does.

        Focus is put on the document body first so tabbing starts at the top of
        the page. Clicking the body instead lands focus wherever the click did
        -- below the total, among the toolbar's checkboxes -- and every Tab from
        there walks further away, past a thousand-odd focusable rows.
        """
        self.browser.execute_script(
            "document.body.setAttribute('tabindex', '-1'); document.body.focus();"
        )
        for _ in range(limit):
            ActionChains(self.browser).send_keys(Keys.TAB).perform()
            if self.browser.switch_to.active_element == target:
                return True
        return False

    def _tip_opacity(self, element):
        """Return the drawn opacity of the tooltip's own box.

        DaisyUI paints the bubble as a `::before` on the wrapper, so nothing in
        the DOM reports whether it is showing; the computed style of the
        pseudo-element is the only place the answer exists.
        """
        return float(
            self.browser.execute_script(
                "return getComputedStyle(arguments[0], '::before').opacity;",
                element,
            )
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_announced_text_follows_the_currency_switch(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The half a screen reader gets, and the bug that made it worth having.

        `setCurrency` wrote `data-tooltip`, which is Materialize's and which
        nothing has read since the conversion -- so the tip was correct as the
        server rendered it and never changed again. A description that goes
        stale is worse than none: it announces a rate no longer on screen.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}
        self.browser.get(f"{self.server_url}/{ADDRESS}")

        total = self.browser.find_element(By.CSS_SELECTOR, ".tooltip[data-tip]")
        note = self.browser.find_element(By.ID, "id-total-tip")
        before = note.get_attribute("textContent")

        self.browser.find_element(
            By.CSS_SELECTOR, ".switch input[type=checkbox]"
        ).click()
        self.wait_until(
            lambda: note.get_attribute("textContent") != before
        )

        self.assertEqual(
            total.get_attribute("data-tip"),
            note.get_attribute("textContent"),
            "the announced description and the visible tip disagree",
        )
        self.assertIn("ALGO/USD", note.get_attribute("textContent"))
