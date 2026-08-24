"""Functional tests for the dynamic NFT section — designs 2 and 3.

The section was design 1's markup bolted to the bottom of this page until now,
and the reason it had to be rebuilt is a measurement: its rows put the value
wherever the text left room, so **the money column stopped at the assets**. That
column is the design. Everything else here follows from bringing the section
into it.

So the load-bearing test in this module is
:meth:`test_the_money_column_runs_to_the_bottom_of_the_page`, which measures one
figure from each of the five levels the page has -- asset header, venue
subtotal, position row, collection header, NFT line -- and requires them to land
on one edge. Nothing short of the laid-out page can check that: every class can
be right while a row is 38px out, which is exactly what the first build of this
section was.

The rest covers what a rebuilt section can quietly lose: the script hooks it
shares with design 1 (`.epoch`, `.nfticon`, `data-src`), and the two numeric
comparisons that a template cannot make correctly because the payload's prices
are decimal strings.
"""

import json
import os
from unittest import mock

from api.position_id import annotate_positions
from django.contrib.auth import get_user_model
from django.core.cache import cache
from selenium.webdriver.common.by import By
from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

from .base import FunctionalTest

SAMPLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "utils",
    "tests",
    "sample_serialized_540A5.json",
)

ADDRESS = "2EVGZ4BGOSL3J64UYDE2BUGTNTBZZZLI54VUQQNZZLYCDODLY33UGXNSIU"
ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]


def _sample_payload():
    """The captured payload, annotated as the view's own path annotates it."""
    with open(SAMPLE_PATH) as sample_file:
        payload = json.load(sample_file)
    for item in payload.get("asaitems", []):
        annotate_positions(item["asset"]["id"], item.get("programs"))
    return payload


class DynamicNftTest(FunctionalTest):
    """The NFT section, rendered as part of this design rather than beside it."""

    def setUp(self):
        super().setUp()
        cache.clear()

    def sign_in(self):
        cookie = self.create_session_cookie(
            username="nfts@example.com", password="top_secret", permission=ASASTATSER
        )
        profile = get_user_model().objects.get(username="nfts@example.com").profile
        profile.preferred_layout = "dynamic"
        profile.save()
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(cookie)

    def open_page(self, collections=2):
        """Load the page and open the first `collections` cards.

        Opened by setting `open` rather than clicking: the summary is a grid and
        a click lands wherever the middle cell happens to be, which on a
        collection row is the name.
        """
        self.record_javascript_errors()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.wait_until(
            lambda: self.browser.execute_script(
                "return !!(window.asastatsToolbar && window.asastatsToolbar.state());"
            )
        )
        self.browser.execute_script(
            "var many = arguments[0];"
            "document.querySelectorAll('#nft-list > .fitem').forEach("
            "  function (card, i) { if (i < many) card.open = true; });",
            collections,
        )

    def right_edge(self, selector):
        """Return the right edge of the first match, in page coordinates."""
        return self.browser.execute_script(
            "var el = document.querySelector(arguments[0]);"
            "if (!el) return null;"
            "var r = el.getBoundingClientRect();"
            "return Math.round(r.right + window.scrollX);",
            selector,
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_money_column_runs_to_the_bottom_of_the_page(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """One figure from each of the five levels, on one edge.

        The whole reason this section was rebuilt. The first build of it had
        every class right and the NFT line 38px out -- it reserved no cell for
        the pin that every other row on the page reserves -- so the column broke
        at exactly the section that was being brought into it.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        self.browser.execute_script(
            "document.querySelectorAll('#asset-list > .fitem').forEach("
            "  function (card, i) { if (i < 2) card.open = true; });"
        )

        levels = {
            "asset header": "#asset-list > .fitem .chead > .cval",
            "venue subtotal": "#asset-list .pgroup-total",
            "position row": "#asset-list .position-row > .position-val",
            "collection header": "#nft-list > .fitem .chead > .cval",
            "NFT line": "#nft-list .nft-line .position-val",
        }
        edges = {name: self.right_edge(css) for name, css in levels.items()}

        self.assertNotIn(None, edges.values(), f"a level did not render: {edges}")
        self.assertEqual(
            1,
            len(set(edges.values())),
            f"the money column does not reach every level: {edges}",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_collection_reads_as_an_asset_row(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Same shell, same height, same place for the figure.

        A collection is a holding. Giving the section its own row idiom is what
        made the two halves of the page read as two pages.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page(collections=0)

        asset = self.browser.find_element(By.CSS_SELECTOR, "#asset-list > .fitem .chead")
        collection = self.browser.find_element(By.CSS_SELECTOR, "#nft-list > .fitem .chead")

        self.assertEqual(
            asset.size["height"],
            collection.size["height"],
            "an asset row and a collection row are different heights",
        )
        self.assertEqual(asset.location["x"], collection.location["x"])
        self.assertEqual(asset.size["width"], collection.size["width"])

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_floor_bar_shows_what_the_estimate_rests_on(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The one fact about a collection a single figure cannot express.

        Measured because it is a ratio drawn as two flex children: the numbers
        can be right in the markup while one side collapses to nothing, which is
        what a `flex: 0` would do to the whole bar.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page(collections=0)

        bars = self.browser.find_elements(By.CSS_SELECTOR, "#nft-list .mix")
        self.assertTrue(bars, "no collection drew a floor bar")

        checked = 0
        for bar in bars[:10]:
            if not bar.is_displayed():
                continue
            floor = bar.find_element(By.CSS_SELECTOR, ".mix-floor")
            rest = bar.find_element(By.CSS_SELECTOR, ".mix-rest")
            with self.subTest(bar=bar.get_attribute("title")[:40]):
                self.assertGreater(bar.size["width"], 0)
                # Both halves are always drawn: a bar with one side missing
                # reads as a bar of a different length rather than as a ratio.
                self.assertGreater(floor.size["width"], 0)
                self.assertGreater(rest.size["width"], 0)
                self.assertAlmostEqual(
                    floor.size["width"] + rest.size["width"],
                    bar.size["width"],
                    delta=4,
                )
            checked += 1

        self.assertGreater(checked, 3, "too few bars to prove anything")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_collection_nobody_floors_says_so_rather_than_showing_zero(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """"floor 0.00" is a different claim from "no marketplace reports one"."""
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page(collections=0)

        chips = [
            chip
            for chip in self.browser.find_elements(
                By.CSS_SELECTOR, "#nft-list .state-chip"
            )
            if chip.is_displayed()
        ]
        if not chips:
            self.skipTest("every collection on this address has a floor")

        card = chips[0].find_element(By.XPATH, "./ancestor::details")
        self.assertIn("no floor reported", card.text)
        self.assertNotIn("floor 0.00", card.text)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_each_figure_says_what_it_is(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """An estimate, a floor and a price paid are three different facts.

        Design 1 renders them as running text with the numbers wherever they
        fall. Here they are a column, and a column of bare figures needs each
        one to carry what it means or it is unreadable.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        item = self.browser.find_element(By.CSS_SELECTOR, "#nft-list .nft-body")
        text = item.text.lower()

        self.assertIn("estimated", text)
        self.assertIn("floor on", text)
        # The comparison the template cannot make itself: both prices are
        # decimal strings and `{% if a > b %}` compares them lexically, so an
        # item worth eight times its floor read as not clearing it.
        self.assertIn("the estimate sits above it", text)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_scripts_still_find_what_they_bind_to(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The hooks this section shares with design 1, exercised.

        `.epoch` is rendered empty and filled by a script, which is design 1's
        arrangement and is kept. What could not be kept is `showTimes` itself:
        it binds to `.nft.item-header` and looks for `.item-body` siblings, and
        this design has neither -- so the section said "Last purchase on Rand
        Gallery" with no indication of when. `dynamic.js` fills them now.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.wait_until(
            lambda: self.browser.execute_script(
                "return !!(window.asastatsToolbar && window.asastatsToolbar.state());"
            )
        )

        self.browser.execute_script(
            "document.querySelector('#nft-list > .fitem').open = true;"
        )

        epochs = self.browser.find_elements(By.CSS_SELECTOR, "#nft-list .epoch")
        if not epochs:
            self.skipTest("the first collection has no purchase history")
        self.wait_until(lambda: epochs[0].text.strip() != "")
        self.assertIn("ago", epochs[0].text.lower())

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_art_is_deferred_and_has_somewhere_to_fall_back_to(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """`deferImages` swaps `data-src` in after load.

        Fifty-five collections of full-size art fetched during page load is the
        reason it exists. The fallback matters as much: NFT media 404s often
        enough that a broken-image glyph would be a routine sight.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        art = self.browser.find_element(By.CSS_SELECTOR, "#nft-list .nft-art img")
        self.assertTrue(art.get_attribute("data-fallback"))
        self.wait_until(lambda: "/thumbnails/" in (art.get_attribute("src") or ""))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_toolbar_reaches_the_section(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Currency and search, which used to be `address.js`'s job here.

        The section is part of this design now, so the toolbar owns its figures.
        Missing it would leave a page half in USD.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page(collections=0)

        figure = self.browser.find_element(By.CSS_SELECTOR, "#nft-list .cval")
        served = figure.text

        self.browser.find_element(By.CSS_SELECTOR, '#tb-ccy [data-ccy="USD"]').click()

        self.wait_until(lambda: "USD" in figure.text)
        self.assertNotEqual(served, figure.text)
        self.assertEqual(1, figure.text.count("USD"), f"unit repeated: {figure.text!r}")

        self.browser.find_element(By.CSS_SELECTOR, '#tb-ccy [data-ccy="ALGO"]').click()
        self.wait_until(lambda: figure.text == served)

        # And the search reaches collections, so filtering for one does not
        # leave the whole section standing beside three matching assets.
        field = self.browser.find_element(By.ID, "tb-q")
        field.send_keys("brave")
        self.wait_until(
            lambda: len(
                [
                    card
                    for card in self.browser.find_elements(
                        By.CSS_SELECTOR, "#nft-list > .fitem"
                    )
                    if card.is_displayed()
                ]
            )
            == 1
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_nft_band_still_hides_the_whole_section(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The fifth category has no positions to filter, so it hides a section.

        Asserted after the rebuild because the control finds the section by
        `.nftsec`, which is a design 1 class the new markup deliberately keeps.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page(collections=0)
        section = self.browser.find_element(By.CSS_SELECTOR, ".dynamic-page .nftsec")
        self.assertTrue(section.is_displayed())

        self.browser.find_element(By.CSS_SELECTOR, '.figs .fig[data-band="nft"]').click()

        self.wait_until(lambda: not section.is_displayed())

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_section_reveals_its_own_batch(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Fifty-five collections, and the load-more rule applies here too --
        with its own, smaller count, because a collection row is taller than an
        asset row and the same number of them is a longer page.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page(collections=0)

        section = self.browser.find_element(By.CSS_SELECTOR, ".dynamic-page .nftsec")
        batch = int(section.get_attribute("data-initial"))
        shown = self._shown()
        self.assertEqual(batch, shown, "the first screen is not the published batch")

        control = section.find_element(By.CSS_SELECTOR, "[data-show-more]")
        control.click()

        # One batch, not the whole tail: fifty-five collections revealed at
        # once is the screen this rule exists to avoid.
        self.wait_until(lambda: self._shown() > shown)
        self.assertEqual(shown + batch, self._shown())
        self.assertEqual([], self.javascript_errors())

    def _shown(self):
        return len(
            [
                card
                for card in self.browser.find_elements(
                    By.CSS_SELECTOR, "#nft-list > .fitem"
                )
                if card.is_displayed()
            ]
        )
