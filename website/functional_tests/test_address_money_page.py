"""Functional tests for the money-column address designs, 2 and 3.

These pages had no functional coverage at all when they shipped, and the
standing rule on this project is that a page we change or add gets functional
tests in the same pass. Everything that actually went wrong while building them
went wrong *in the browser*: an allocation figure reading 0.00 when it was 79%
of the address, a Tailwind utility that was never compiled because the build ran
before the template was written, a class name colliding with DaisyUI's `.stack`
so five bar segments stacked into one. None of those fail a template test, which
asserts on markup the server produced and is happy either way.

So the assertions here are about what a reader can see and do, and several of
them are measurements rather than lookups.

**What the design is.** One money column. Asset headers, venue subtotals and
position rows put their figure in a cell `--col` wide at the same x, so a reader
compares down the page instead of across it. `test_the_money_column_lines_up`
measures that, because it is the one property of this design that cannot be
checked by reading the markup -- the classes can all be present and correct
while the column is 8px out.

**Who gets it.** The layout is a subscription benefit gated at Asastatser, and
the gate is re-checked on read, so a lapsed reader falls back to design 1 with
their choice remembered. Both halves of that are asserted, because the failure
mode of the first is paid bytes handed to a free reader, and of the second a
reader who paid and sees the old page.

Two traps, both of which cost time before they were written down:

* **The cache.** The address page is cached per `(address, layout)` and
  `pytest.ini` pins `config.settings.automated_tests`, which uses a real
  LocMemCache. An entry left behind by an earlier test is served to the next one
  and its mocked payload is never consulted, so every test here clears the cache
  in `setUp`. Under `config.settings.development` the cache is a `DummyCache`
  and this problem is invisible -- which is exactly why it needs saying.
* **Folding.** The tail of the asset list past the load-more cutoff is
  `display: none`, and a hidden row has no geometry: every measurement below
  would read zero and compare it against zero. `_open_page` unfolds first.
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

#: The tier the money-column layouts are gated at.
ASASTATSER = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]


def _sample_payload():
    """The captured bundle payload, in the shape the view actually receives.

    The file predates ``pid``, which ``AsaItemSerializer`` now adds on the way
    out of the internal API. Mocking ``fetch_and_serialize_account`` replaces
    the serializer, so without annotating here every position would render
    without an identity -- no pin control anywhere on the page, and the pinning
    tests below would skip themselves rather than fail. The unit tests annotate
    it for the same reason; see ``_build_context`` in
    ``core/tests/test_address_templates.py``.
    """
    with open(SAMPLE_PATH) as sample_file:
        payload = json.load(sample_file)
    for item in payload.get("asaitems", []):
        annotate_positions(item["asset"]["id"], item.get("programs"))
    return payload


class MoneyPageMixin:
    """Signing a reader in on a chosen layout, and opening the page."""

    def setUp(self):
        super().setUp()
        # See the module docstring: a real cache under the automated settings,
        # keyed on (address, layout), will happily serve this test the page an
        # earlier one rendered from a different payload.
        cache.clear()

    def sign_in(self, email, permission, layout):
        """Sign a reader in carrying ``permission`` and preferring ``layout``.

        The layout is written straight onto the profile rather than posted
        through the settings form: what is under test here is the page, and
        going through the form would make every one of these tests fail when
        the form changes.
        """
        cookie = self.create_session_cookie(
            username=email, password="top_secret", permission=permission
        )
        profile = get_user_model().objects.get(username=email).profile
        profile.preferred_layout = layout
        profile.save()

        # A 404 loads quickest, and a page has to be open before a cookie can
        # be set for the domain.
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(cookie)

    def open_address(self):
        """Load the address page for whoever is signed in."""
        self.browser.get(f"{self.server_url}/{ADDRESS}")

    def computed(self, element, prop):
        return self.browser.execute_script(
            "return getComputedStyle(arguments[0])[arguments[1]];", element, prop
        )

    def right_edge(self, element):
        """Return the element's right edge in page coordinates.

        Selenium's ``location``/``size`` round to integers, which is enough to
        hide a sub-pixel drift and not enough to hide a real one; the client
        rect is what the browser actually laid out.
        """
        return self.browser.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return r.right + window.scrollX;",
            element,
        )


class MoneyColumnEntitlementTest(MoneyPageMixin, FunctionalTest):
    """Design 1 for everybody; designs 2 and 3 for subscribers.

    The layout registry gates both money-column entries at Asastatser and
    ``Profile.preferred_layout_or_default`` re-checks that on every read, so
    these two tests are the top and the bottom of the same gate.
    """

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_subscriber_sees_the_money_column(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}

        # Sam subscribes at Asastatser and has chosen the money column.
        self.sign_in("sam-money@example.com", ASASTATSER, "money-column")
        self.open_address()

        # He gets it: the design's own scope class, and asset rows built the
        # money-column way rather than design 1's.
        self.assertTrue(self.browser.find_elements(By.CSS_SELECTOR, ".money-page"))
        self.assertTrue(self.browser.find_elements(By.CSS_SELECTOR, ".chead"))

        # And not design 1, whose consolidated block and chart canvases are
        # absent here -- this design draws its own charts.
        self.assertFalse(self.browser.find_elements(By.CSS_SELECTOR, "div.consolidated"))
        self.assertFalse(self.browser.find_elements(By.TAG_NAME, "canvas"))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_reader_below_the_tier_still_gets_design_one(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The saved choice is kept, and it does not apply.

        This is the shape of a lapsed subscription: the preference is still on
        the profile, waiting for a renewal, and the page resolves to the
        default because entitlement is re-checked on read. Getting it wrong the
        other way hands a free reader a paid design.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": 0}

        # Fay's subscription has lapsed, but her choice is still stored.
        self.sign_in("fay-free@example.com", 0, "money-column")
        self.open_address()

        self.assertFalse(self.browser.find_elements(By.CSS_SELECTOR, ".money-page"))
        # She gets the page everybody gets, in full.
        self.assertTrue(self.browser.find_elements(By.CSS_SELECTOR, "div.consolidated"))

        # The choice is remembered rather than cleared, so a renewal restores it.
        profile = get_user_model().objects.get(username="fay-free@example.com").profile
        self.assertEqual("money-column", profile.preferred_layout)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_money_column_does_not_ship_chartjs(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """~200 KB a reader of this design never needs.

        The charts here are inline SVG drawn by `money.js`. The saving is only
        real if the bundle is genuinely absent from the page, which the template
        alone cannot promise -- `base.html` could start including it tomorrow
        and every template test would stay green.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}

        self.sign_in("chart-free@example.com", ASASTATSER, "money-column")
        self.open_address()

        sources = [
            script.get_attribute("src") or ""
            for script in self.browser.find_elements(By.TAG_NAME, "script")
        ]
        self.assertFalse(
            [src for src in sources if "chart.min" in src],
            f"the money column pulled in Chart.js: {sources}",
        )
        self.assertTrue([src for src in sources if src.endswith("money.js")])


class MoneyColumnStructureTest(MoneyPageMixin, FunctionalTest):
    """What the page shows, and what a reader can do with it."""

    #: Asset rows only. The NFT section is still design 1's `snippets/nfts.html`
    #: and its collections are `details.fitem` too, so an unscoped selector
    #: picks up rows that have no money column, no venue groups and no `.cval`.
    ASSETS = "#asa-section .rows > details.fitem"

    def _sign_in(self):
        """Sign in as a subscriber on the money column.

        Called from inside each test rather than from `setUp`, because `setUp`
        runs *before* the mock decorators are applied -- so the page load it
        performs reaches for the capabilities API on :8001 and logs a
        connection error that has nothing to do with what is being tested.
        """
        self.sign_in("struct-money@example.com", ASASTATSER, "money-column")

    def _open_page(self):
        """Load the page with the folded tail revealed and images settled.

        Both steps are load-bearing for the measurements below. The rows past
        the load-more cutoff are `display: none` and have no geometry at all,
        and `deferImages` assigns every `src` after load -- so a thumbnail that
        arrives mid-measurement pushes everything below it down, and a
        coordinate read before that compares against one the page has already
        replaced.

        The fold is clicked rather than styled around, so the control itself is
        exercised on the way to everything else here.
        """
        self.open_address()
        self.browser.execute_script(
            "document.querySelectorAll('[data-show-more]')"
            ".forEach(function (button) { button.click(); });"
        )
        self.wait_until(
            lambda: self.browser.execute_script(
                "return Array.prototype.every.call("
                "  document.images, function (img) { return img.complete; });"
            )
        )

    def _open_first_asset(self):
        """Open the first asset row and return its `<details>`.

        Opened by setting `open` rather than by clicking the summary: the
        summary is a five-cell grid and a click lands wherever the middle cell
        happens to be, which on a narrow row is a link that navigates away.
        """
        card = self.browser.find_element(By.CSS_SELECTOR, self.ASSETS)
        self.browser.execute_script("arguments[0].open = true;", card)
        return card

    def _open_every_asset(self):
        """Open every asset row on the page.

        The first asset is usually ALGO itself -- one wallet balance, no venue
        to group it under, no breakdown to open and no stable position id to
        pin. A test that only ever opens that one skips itself, and a skip
        reads exactly like a pass while covering nothing. Three of these did
        that before they were pointed at the whole list.
        """
        self.browser.execute_script(
            "document.querySelectorAll(arguments[0])"
            ".forEach(function (card) { card.open = true; });",
            self.ASSETS,
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_money_column_lines_up(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The one claim of this design, measured.

        Every venue subtotal and every position figure inside an opened asset
        has to end at the same x, or a reader cannot see four venue figures
        adding up to the asset's own. The markup can be entirely correct while
        this is false -- one stray `padding-right` on the row is enough -- so
        nothing short of the laid-out geometry tests it.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self._open_page()
        card = self._open_first_asset()

        subtotals = card.find_elements(By.CSS_SELECTOR, ".pgroup-total")
        figures = card.find_elements(By.CSS_SELECTOR, ".position-row > .position-val")
        self.assertTrue(subtotals, "the opened asset shows no venue subtotals")
        self.assertTrue(figures, "the opened asset shows no position figures")

        edges = {
            round(self.right_edge(cell)) for cell in list(subtotals) + list(figures)
        }
        self.assertEqual(
            1,
            len(edges),
            f"the money column is not one column: right edges {sorted(edges)}",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_every_asset_header_puts_its_figure_in_the_same_column(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Down the closed list, the same edge on every row.

        Separate from the test above because it is a different grid -- the
        asset header is five cells and the position row is three -- and they
        can drift apart independently.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self._open_page()

        values = self.browser.find_elements(By.CSS_SELECTOR, ".chead > .cval")
        self.assertGreater(len(values), 1, "one row proves no alignment")

        edges = {round(self.right_edge(cell)) for cell in values}
        self.assertEqual(
            1, len(edges), f"asset figures wandered: right edges {sorted(edges)}"
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_venue_subtotals_add_up_to_the_asset_value(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The reason for grouping at all.

        A reader holding one asset in nine places is asking how much of it is
        on each venue. If the subtotals do not sum to the figure in the header
        above them, the grouping has invented an answer -- which is worse than
        the flat list it replaced.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self._open_page()

        cards = self.browser.find_elements(By.CSS_SELECTOR, self.ASSETS)
        self.assertTrue(cards, "the page rendered no assets")

        checked = 0
        for card in cards:
            self.browser.execute_script("arguments[0].open = true;", card)
            header = card.find_element(By.CSS_SELECTOR, ".chead .cval .val")
            subtotals = card.find_elements(By.CSS_SELECTOR, ".pgroup-total")
            if not subtotals:
                continue
            total = float(header.get_attribute("data-val"))
            summed = sum(
                float(cell.get_attribute("data-val")) for cell in subtotals
            )
            with self.subTest(asset=card.get_attribute("id")):
                # A tenth of an ALGO: the payload's own values are floats and
                # the sum of a dozen of them is not bit-identical to the total
                # the engine computed. A grouping fault is never this small.
                self.assertAlmostEqual(
                    total,
                    summed,
                    delta=0.1,
                    msg=f"header {total} vs venues {summed}",
                )
            checked += 1

        self.assertGreater(checked, 0, "no asset carried a venue group to check")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_fold_hides_the_tail_until_it_is_asked_for(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The load-more control, exercised as a reader meets it.

        The rows are all in the document either way -- this only flips which
        are displayed -- so a test reading the markup sees the whole list
        whether the fold works or not.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self.open_address()

        folded = self.browser.find_elements(By.CSS_SELECTOR, ".rows .fitem.folded")
        if not folded:
            self.skipTest("the sample address is short enough to need no fold")

        self.assertFalse(
            any(row.is_displayed() for row in folded),
            "the folded tail was on screen before anything asked for it",
        )

        control = self.browser.find_element(By.CSS_SELECTOR, "[data-show-more]")
        self.assertEqual("false", control.get_attribute("aria-expanded"))
        control.click()

        self.wait_until(lambda: all(row.is_displayed() for row in folded))
        # The button owns the state, and the stylesheet reads it for both the
        # rows and the button's own label -- so the attribute is the assertion.
        self.assertEqual("true", control.get_attribute("aria-expanded"))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_pinning_a_position_puts_a_card_in_the_band(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The band is empty markup until the reader's own browser fills it.

        It cannot be rendered server-side: this page's cache entry is shared by
        every reader on the layout, so one reader's pins would be handed to the
        next. That makes the band a browser-only feature end to end, and this
        the only kind of test that sees it work.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self._open_page()
        self._open_every_asset()

        band = self.browser.find_element(By.ID, "pinned-section")
        self.assertFalse(band.is_displayed(), "the band showed before anything was pinned")

        pin = self.browser.find_element(By.CSS_SELECTOR, "[data-pin-position]")
        # Read the way `pins.js` reads it: off the `.position` wrapper, whose
        # first `.position-label` is the row's own -- a breakdown underneath
        # carries labels of its own and they are not what was pinned.
        label = self.browser.execute_script(
            "return arguments[0].closest('.position')"
            ".querySelector('.position-label').textContent.trim();",
            pin,
        )
        pin.click()

        self.wait_until(lambda: band.is_displayed())
        cards = self.browser.find_elements(By.CSS_SELECTOR, "#pin-grid .pin-card")
        self.assertEqual(1, len(cards), "the band did not take exactly one card")
        # The card names the position it came from, so the reader can tell what
        # they pinned without scrolling back to it.
        self.assertEqual(label, cards[0].find_element(By.CSS_SELECTOR, ".position-label").text.strip())
        self.assertEqual("1", self.browser.find_element(By.ID, "pin-count").text.strip())
        self.assertEqual("true", pin.get_attribute("aria-pressed"))

        # And the card's own control puts it back.
        cards[0].find_element(By.CSS_SELECTOR, "[data-unpin-position]").click()
        self.wait_until(lambda: not band.is_displayed())
        self.assertEqual("false", pin.get_attribute("aria-pressed"))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_pin_survives_a_reload(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Remembered in the reader's browser, which is the whole promise.

        A pin that vanishes on reload is not a pin. Worth its own test because
        the round trip crosses the part that cannot be rendered: the page comes
        back off a shared cache entry knowing nothing about this reader, and
        `pins.js` has to rebuild the band from `localStorage` alone.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self._open_page()
        self._open_every_asset()

        self.browser.find_element(By.CSS_SELECTOR, "[data-pin-position]").click()
        self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, "#pin-grid .pin-card")
        )

        self._open_page()

        self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, "#pin-grid .pin-card")
        )
        band = self.browser.find_element(By.ID, "pinned-section")
        self.assertTrue(band.is_displayed(), "the pinned band did not come back")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_charts_panel_draws_its_donuts_on_first_open(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Empty markup by design, filled by `money.js` when asked.

        An SVG for six charts is a great deal of bytes to ship to every reader
        who never opens the panel, so the grid ships empty -- which means a
        template test can only ever see an empty div here.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self.open_address()

        grid = self.browser.find_element(By.ID, "charts-grid")
        self.assertFalse(
            grid.find_elements(By.TAG_NAME, "svg"),
            "the charts drew before the panel was opened",
        )

        self.browser.find_element(By.CSS_SELECTOR, "#charts > summary").click()

        self.wait_until(lambda: grid.find_elements(By.TAG_NAME, "svg"))
        charts = grid.find_elements(By.TAG_NAME, "svg")
        self.assertGreater(len(charts), 1, "only one chart drew")
        # A ring, not a filled circle: `money.js` draws each donut as two
        # circles with `fill-rule="evenodd"`, because a full ring cannot be one
        # arc -- SVG collapses a 360 degree arc to nothing.
        self.assertTrue(
            charts[0].find_elements(By.CSS_SELECTOR, "[fill-rule='evenodd'], circle"),
            "the donut drew without the shape that makes it a donut",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_allocation_bar_and_its_figures_tell_the_same_story(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Three drawings of one set of numbers must not disagree.

        Measured rather than read off the markup because the fault this catches
        is a layout one. `.stack` -- the class this bar first carried -- is
        DaisyUI's, and it puts every child in the same grid area: five segments
        with correct widths in the markup, rendered as one segment covering the
        other four. The reader sees a bar claiming 100% balance.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self.open_address()

        bar = self.browser.find_element(By.ID, "allocation-bar")
        segments = bar.find_elements(By.CSS_SELECTOR, "[data-band]")
        self.assertGreater(len(segments), 1, "the bar drew a single category")

        # Side by side, not on top of each other: each segment starts where the
        # one before it ended.
        edges = [self.right_edge(segment) for segment in segments]
        self.assertEqual(
            edges, sorted(edges), f"the segments are stacked, not laid out: {edges}"
        )
        # And together they reach the full width -- a gap at the right-hand end
        # reads as money that went missing.
        self.assertAlmostEqual(edges[-1], self.right_edge(bar), delta=2)

        # The figures beside the bar carry the same shares the bar was drawn
        # from, so a reader cannot see the two disagree.
        widths = {
            segment.get_attribute("data-band"): segment.size["width"]
            for segment in segments
        }
        shares = {
            fig.get_attribute("data-band"): float(
                fig.find_element(By.CSS_SELECTOR, ".fig-share").text.rstrip("%")
            )
            for fig in self.browser.find_elements(By.CSS_SELECTOR, ".figs .fig")
        }
        # Against the drawn segments' own sum, not the bar's width: the bar
        # separates its segments with a 2px gap, so five categories give up 8px
        # of a ~1230px bar before any of them is drawn. Measuring against the
        # container reports every band as ~0.65% short of its figure, which
        # says nothing about whether the two agree.
        drawn = sum(widths.values())
        compared = 0
        for key, width in widths.items():
            # `min-width: 3px` is a visibility floor: a band too small to draw
            # at its true share is drawn at the floor on purpose, so that it can
            # be seen at all. Comparing those to their figure would be testing
            # the floor.
            if width <= 3.5:
                continue
            compared += 1
            with self.subTest(band=key):
                self.assertAlmostEqual(
                    width / drawn * 100, shares[key], delta=0.5,
                    msg=f"{key}: bar {width / drawn * 100:.2f}% vs figure {shares[key]}%",
                )
        self.assertGreater(compared, 1, "fewer than two bands were big enough to check")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_figure_with_a_breakdown_says_so_before_it_is_clicked(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The two link idioms have to be distinguishable at rest.

        A reader deciding where to click has not pointed at anything yet, so a
        difference that only appears on hover is no difference at all. `.tdist`
        opens the breakdown in place and is dotted at rest; `.out` leaves the
        site. A plain figure is just a figure.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self._sign_in()
        self._open_page()
        self._open_every_asset()

        opener = self.browser.find_element(By.CSS_SELECTOR, ".amt.tdist")

        self.assertIn(
            "dotted",
            self.computed(opener, "borderBottomStyle")
            + self.computed(opener, "textDecorationStyle"),
            "the breakdown control is indistinguishable from a plain figure",
        )

        breakdown = self.browser.find_element(
            By.ID, opener.get_attribute("data-distid")
        )
        self.assertFalse(breakdown.is_displayed())
        self.assertEqual("false", opener.get_attribute("aria-expanded"))

        opener.click()

        self.wait_until(lambda: breakdown.is_displayed())
        self.assertEqual("true", opener.get_attribute("aria-expanded"))


class MoneyColumnCompactTest(MoneyPageMixin, FunctionalTest):
    """Design 3: the same template, one class, a different list.

    `compact` comes off the layout registry and adds `.rows.cards`, which turns
    the single stacked column into a tile grid. One template renders both, so
    the only thing that can break this is the stylesheet -- and the only place
    the difference exists is the laid-out page.
    """

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_compact_layout_puts_the_rows_side_by_side(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}

        self.sign_in("compact@example.com", ASASTATSER, "money-column-compact")
        self.open_address()

        rows = self.browser.find_element(By.CSS_SELECTOR, ".rows")
        self.assertIn("cards", rows.get_attribute("class"))
        self.assertEqual("grid", self.computed(rows, "display"))

        tops = [
            card.location["y"]
            for card in rows.find_elements(By.CSS_SELECTOR, ".mcard")
            if card.is_displayed()
        ]
        self.assertGreater(len(tops), 1, "one tile proves no grid")
        self.assertLess(
            len(set(tops)),
            len(tops),
            f"every tile is on a line of its own, so this is not compact: {tops}",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_wide_layout_gives_each_asset_its_own_line(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The other half of the pair, so the test above proves a difference.

        Asserting only that the compact list wraps would pass if both layouts
        wrapped -- which would mean the compact flag does nothing.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}

        self.sign_in("wide@example.com", ASASTATSER, "money-column")
        self.open_address()

        rows = self.browser.find_element(By.CSS_SELECTOR, ".rows")
        self.assertNotIn("cards", rows.get_attribute("class"))

        tops = [
            card.location["y"]
            for card in rows.find_elements(By.CSS_SELECTOR, ".mcard")
            if card.is_displayed()
        ]
        self.assertGreater(len(tops), 1, "one row proves nothing")
        self.assertEqual(
            len(set(tops)), len(tops), f"two assets shared a line: {tops}"
        )
