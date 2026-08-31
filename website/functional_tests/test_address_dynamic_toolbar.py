"""Functional tests for the dynamic toolbar — pass 2 of designs 2 and 3.

The toolbar is entirely a browser feature: it filters, sorts, regroups and
re-denominates a page that is already in the reader's hands, and the server
never learns any of it. So there is no server-rendered markup to assert on, and
its jest suite -- 87 tests, 100% -- drives a synthetic DOM built to the shape
the templates *should* produce. Neither can tell you the templates actually
produce that shape, or that the four scripts sharing this page cooperate.

Both of those went wrong while it was being built, and both are here:

* **`address.js` was mangling the money column on every load.** Its
  `setCurrency` writes `innerHTML` -- number and unit together -- into every
  `span.val`, which is right for design 1, where the unit is part of the value's
  text. Here each figure pairs with a *separate* unit element, so the asset
  header read "253.74 ALGO ALGO" and every venue subtotal lost its nested
  `<span class="unit">`. It ran unconditionally, so it was live for every reader
  of designs 2 and 3, and no test anywhere looked at a rendered unit.
* **Restoring the asset grouping threw**, because the venue view remembered
  each group's next *sibling* -- and an asset holding four venues has all four
  moved away, so the node to insert before had itself gone.

The measurements below are the ones the design's own promises rest on: that the
headline never moves, that the subtotals still add up after filtering, and that
a pinned row survives a sort.
"""

import json
import os
import re
from unittest import mock

from api.position_id import annotate_positions
from django.contrib.auth import get_user_model
from django.core.cache import cache
from selenium.webdriver.common.action_chains import ActionChains
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

#: A money figure: grouped digits and exactly two decimals. Both ways of
#: writing a negative are allowed - this design uses parentheses in the
#: templates and a leading minus once the toolbar has repainted - because what
#: is under test is the number of decimal places, not the sign convention.
_TWO_DECIMALS = re.compile(r"^\(?-?[\d,]*\d\.\d{2}\)?$")


def _sample_payload():
    """The captured payload, annotated the way the view's own path annotates it.

    See ``test_address_dynamic_page.py``: mocking ``fetch_and_serialize_account``
    replaces the layer that adds ``pid``, so without this no position carries an
    identity and the pinning half of these tests would pass vacuously.
    """
    with open(SAMPLE_PATH) as sample_file:
        payload = json.load(sample_file)
    for item in payload.get("asaitems", []):
        annotate_positions(item["asset"]["id"], item.get("programs"))
    return payload


class ToolbarTest(FunctionalTest):
    """Driving the toolbar in a browser, against the real templates."""

    def setUp(self):
        super().setUp()
        # The page is cached per (address, layout) and the automated settings
        # use a real LocMemCache; an entry from an earlier test would be served
        # and this test's payload never consulted.
        cache.clear()

    def sign_in(self):
        cookie = self.create_session_cookie(
            username="toolbar@example.com", password="top_secret", permission=ASASTATSER
        )
        profile = get_user_model().objects.get(username="toolbar@example.com").profile
        profile.preferred_layout = "dynamic"
        profile.save()
        self.browser.get(self.server_url + "/404.html")
        self.browser.add_cookie(cookie)

    def open_page(self):
        """Load the page and wait for the toolbar to have applied itself."""
        self.record_javascript_errors()
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.wait_until(
            lambda: self.browser.execute_script(
                "return !!(window.asastatsToolbar && window.asastatsToolbar.state());"
            )
        )

    # -- helpers ------------------------------------------------------------

    def press(self, selector):
        self.browser.find_element(By.CSS_SELECTOR, selector).click()

    def filter_for(self, text):
        field = self.browser.find_element(By.ID, "tb-q")
        field.clear()
        field.send_keys(text)
        self.wait_until(lambda: self.status() != "")

    def status(self):
        return self.browser.find_element(By.ID, "tb-status").text.strip()

    def shown(self, selector="#asset-list > .fitem"):
        """Ids of the rows a reader can actually see."""
        return [
            row.get_attribute("id")
            for row in self.browser.find_elements(By.CSS_SELECTOR, selector)
            if row.is_displayed()
        ]

    def headline(self):
        return self.browser.find_element(By.CSS_SELECTOR, ".dynamic-page h1.total").text

    def open_assets(self):
        self.browser.execute_script(
            "document.querySelectorAll('#asset-list > .fitem')"
            ".forEach(function (card) { card.open = true; });"
        )

    # -- tests --------------------------------------------------------------

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_toolbar_arrives_without_a_script_error(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Four scripts share this page and each re-arranges what the last did.

        A thrown exception in any of them leaves the page looking rendered and
        every control dead, which is the failure this suite exists to catch
        before a reader does.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        self.assertEqual([], self.javascript_errors())
        self.assertTrue(self.browser.find_element(By.ID, "toolbar").is_displayed())
        self.assertEqual("", self.status(), "an untouched page announced a filter")
        self.assertTrue(self.browser.find_element(By.ID, "tb-reset").get_attribute("disabled"))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_no_filter_moves_the_headline(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A reader who hides a category has not become poorer.

        The headline is what the address is worth, not a readout of the current
        view. Everything below it is a subtotal and is free to respond.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        served = self.headline()
        self.assertIn("ALGO", served)

        self.filter_for("usdc")
        self.assertEqual(served, self.headline())

        self.press('.figs .fig[data-band="defi"]')
        self.assertEqual(served, self.headline())

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_headline_follows_the_currency(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A currency is not a filter.

        It is the unit the whole page is denominated in, and a page whose every
        figure says USD above a total that says ALGO is not showing a total at
        all. Readers of design 1 have always had the total switch with
        everything else.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        self.assertIn("ALGO", self.headline())

        self.press('#tb-ccy [data-ccy="USD"]')

        self.wait_until(lambda: "USD" in self.headline())
        self.assertNotIn("ALGO", self.headline())
        self.assertEqual(1, self.headline().count("USD"))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_currency_chosen_anywhere_is_the_currency_here(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The second half of the same complaint.

        The choice was stored per address, while design 1 stores it globally --
        so a reader who picked USD on design 1 opened this page to a USD
        headline (written by `address.js` on load) above ALGO figures, and a
        second tab disagreed with the first. One key, both designs.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.browser.execute_script("window.localStorage.setItem('cur', 'USD');")

        self.open_page()

        self.assertIn("USD", self.headline())
        self.assertNotIn("ALGO", self.headline())
        self.assertEqual(
            "true",
            self.browser.find_element(
                By.CSS_SELECTOR, '#tb-ccy [data-ccy="USD"]'
            ).get_attribute("aria-pressed"),
        )
        header = self.browser.find_element(By.CSS_SELECTOR, "#asset-list .chead .cval")
        self.assertIn("USD", header.text)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_total_can_leave_the_nfts_out(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Design 1 has this and the money column was missing it.

        A legitimate move of the headline, because it changes *what is being
        totalled* rather than how it is shown -- and on the reference address
        the NFTs are 79% of it, so the two readings are different answers to
        different questions.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        whole = self._number(self.headline().split()[-2])

        self.press("#tb-nonft")

        self.wait_until(lambda: self._number(self.headline().split()[-2]) < whole)
        self.assertIn(
            "except the NFTs",
            self.browser.find_element(By.CSS_SELECTOR, ".total-note").text,
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_hiding_a_category_says_what_the_rest_comes_to(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The headline holding still leaves a question unanswered.

        A reader who switches DeFi off can see that the total did not move --
        which is right -- and had no way to see what the remaining categories
        add up to. That is what the band's readout is for, and it appears only
        when it differs from the headline.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        readout = self.browser.find_element(By.ID, "band-readout")
        self.assertEqual("", readout.text.strip(), "an unfiltered page announced a total")

        self.press('.figs .fig[data-band="defi"]')

        self.wait_until(lambda: readout.text.strip() != "")
        self.assertRegex(readout.text, r"^Showing [\d,.]+ ALGO of [\d,.]+ ALGO$")
        shown, whole = [
            self._number(part) for part in readout.text.replace(",", "").split()[1::3]
        ]
        self.assertLess(shown, whole)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_auto_refresh_is_offered_again(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Design 1 has it; this design was missing it.

        The timer that acts on it is `address.js`'s and is already running on
        this page, so what was missing was only the control and the key.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        self.press("#tb-refresh")

        self.wait_until(
            lambda: self.browser.execute_script(
                "return window.localStorage.getItem('refresh');"
            )
            == "y"
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_pressed_toggle_looks_pressed(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A reader can see which of the on/off controls are on.

        `toolbar.js` has always set `aria-pressed` on these two, and for a while
        that was the whole of the feedback: `.ghost` had rules for rest, hover
        and disabled and none for the pressed state, so a screen reader was told
        which was on and everybody else was told nothing.

        Auto-refresh is where it hurt. It reloads only after 60 seconds of
        inactivity, so with no visible state there is nothing to distinguish
        "on, and waiting for you to stop moving the mouse" from a dead button --
        which is exactly how it was reported.

        Asserted through the *computed* style rather than the class list,
        because a class that no rule matches is the failure being guarded
        against. `aria-pressed` is checked too: the two have to move together or
        the announcement and the appearance disagree.

        **The pointer is moved off the button before the second reading.** The
        first version of this test did not do that and passed with the pressed
        rule deleted: clicking leaves the cursor on the control, `.ghost:hover`
        also changes the background, and the before/after comparison was
        measuring the hover. It is compared against a sibling ghost that was
        never pressed for the same reason -- two readings of one element can
        differ for reasons that have nothing to do with state.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        def unhovered_style(selector):
            """Return the button's colours with the pointer parked elsewhere."""
            ActionChains(self.browser).move_to_element(
                self.browser.find_element(By.CSS_SELECTOR, "#tb-q")
            ).perform()
            button = self.browser.find_element(By.CSS_SELECTOR, selector)
            return (
                button.value_of_css_property("background-color"),
                button.value_of_css_property("color"),
            )

        for selector in ("#tb-refresh", "#tb-nonft"):
            with self.subTest(control=selector):
                self.assertEqual(
                    self.browser.find_element(
                        By.CSS_SELECTOR, selector
                    ).get_attribute("aria-pressed"),
                    "false",
                )
                resting = unhovered_style(selector)

                self.press(selector)
                self.wait_until(
                    lambda: self.browser.find_element(
                        By.CSS_SELECTOR, selector
                    ).get_attribute("aria-pressed")
                    == "true"
                )
                pressed = unhovered_style(selector)

                self.assertNotEqual(
                    resting,
                    pressed,
                    f"{selector} looks identical pressed and unpressed, so "
                    "nothing on screen says it is on",
                )
                self.assertNotEqual(
                    pressed,
                    unhovered_style("#tb-dir"),
                    f"{selector} pressed looks like an unpressed ghost beside "
                    "it, so the tint is not doing any work",
                )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_searching_narrows_the_list_and_says_so(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        before = len(self.shown())

        self.filter_for("usdc")

        after = self.shown()
        self.assertGreater(before, len(after))
        self.assertTrue(after, "the filter matched nothing at all")
        # Announced, because filtering changes the page without moving focus --
        # which a screen reader is otherwise never told about.
        self.assertRegex(self.status(), r"^Showing \d+ of \d+ assets\.$")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_currency_switch_leaves_one_unit_per_figure(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The regression that was live on this design.

        `address.js` wrote the unit into the value's own text while the sibling
        unit element kept saying ALGO, so every asset header read "253.74 ALGO
        ALGO"; and it replaced a venue subtotal's `innerHTML` wholesale, which
        destroyed the nested unit span. Both are invisible to a template test --
        the markup the server produced was correct throughout.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        self.open_assets()

        header = self.browser.find_element(By.CSS_SELECTOR, "#asset-list .chead .cval")
        self.assertEqual(
            1,
            header.text.count("ALGO"),
            f"the asset header names its unit more than once: {header.text!r}",
        )

        subtotal = self.browser.find_element(By.CSS_SELECTOR, "#asset-list .pgroup-total")
        self.assertEqual(
            1,
            len(subtotal.find_elements(By.CSS_SELECTOR, ".unit")),
            "the venue subtotal lost or gained a unit element",
        )

        self.press('#tb-ccy [data-ccy="USD"]')

        self.wait_until(lambda: "USD" in header.text)
        self.assertEqual(1, header.text.count("USD"))
        self.assertNotIn("ALGO", header.text)
        self.assertEqual("USD", subtotal.find_element(By.CSS_SELECTOR, ".unit").text)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_money_column_is_two_decimals_in_either_currency(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A money column has one shape, and money has two decimals.

        `fmt` used to widen anything under half a cent to *six* places, so that
        a small borrowing did not round to "0.00" and read as nothing owed. It
        did it to every dust holding as well - nine of them on this fixture -
        and a six-decimal figure sitting in a column of two-decimal ones reads
        as the larger number until you stop and count digits: 0.004574 under
        1,284.02.

        Browser-only in both directions. The server renders these cells with
        `floatformat:'2g'` and always did, so a template test sees two decimals
        whatever the script does; and the widening only appeared once
        `paintFigures` had repainted the column, which is after load and again
        on every filter and currency press.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        self.open_assets()

        # cAlgo is worth 0.000042 ALGO on this address - one of nine holdings
        # under half a cent, which is what the old rule widened.
        dust = self.browser.find_element(
            By.CSS_SELECTOR, "#f2400334372 .cval .val"
        )
        # `textContent`, not `.text`: this row is past the first batch and
        # therefore folded, and Selenium reads a hidden element as "".
        self.assertEqual("0.00", dust.get_attribute("textContent").strip())

        for currency in ("ALGO", "USD"):
            with self.subTest(currency=currency):
                if currency == "USD":
                    self.press('#tb-ccy [data-ccy="USD"]')
                    self.wait_until(
                        lambda: "USD"
                        in self.browser.find_element(
                            By.CSS_SELECTOR, "#asset-list .chead .cval"
                        ).text
                    )
                figures = self.browser.find_elements(
                    By.CSS_SELECTOR, "#asset-list .cval .val"
                )
                self.assertTrue(figures, "no money column to measure")
                wrong = [
                    text
                    for text in (
                        figure.get_attribute("textContent").strip()
                        for figure in figures
                    )
                    if not _TWO_DECIMALS.match(text)
                ]
                self.assertEqual(
                    [],
                    wrong,
                    f"{currency} figures are not written to two decimals: {wrong}",
                )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_category_control_dims_rather_than_disappearing(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """A segment filtered to zero width would have no box left to press.

        So a switched-off category keeps its real value and its width, and goes
        quiet instead. Measured, because "goes quiet" is a computed opacity and
        "keeps its width" is geometry -- the markup is identical either way.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        figure = self.browser.find_element(
            By.CSS_SELECTOR, '.figs .fig[data-band="liquidity"]'
        )
        segment = self.browser.find_element(
            By.CSS_SELECTOR, '#allocation-bar [data-band="liquidity"]'
        )
        served = figure.find_element(By.CSS_SELECTOR, ".fig-val").text
        width = segment.size["width"]

        figure.click()

        self.wait_until(lambda: figure.get_attribute("aria-pressed") == "false")
        self.assertEqual(
            served,
            figure.find_element(By.CSS_SELECTOR, ".fig-val").text,
            "the figure zeroed itself, which reads as holding none",
        )
        self.assertEqual(width, segment.size["width"])
        self.assertGreater(segment.size["width"], 0, "the segment cannot be pressed again")
        # Waited for rather than read straight after the press: the dim is a
        # 0.12s transition, so reading immediately catches it at full opacity
        # and reports a working control as broken.
        self.wait_until(
            lambda: float(segment.value_of_css_property("opacity")) < 1.0
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_bar_and_the_figure_are_one_control(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Three drawings of one set of numbers cannot disagree."""
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        self.press('#allocation-bar [data-band="staked"]')

        figure = self.browser.find_element(By.CSS_SELECTOR, '.figs .fig[data-band="staked"]')
        self.wait_until(lambda: figure.get_attribute("aria-pressed") == "false")

        figure.click()

        segment = self.browser.find_element(
            By.CSS_SELECTOR, '#allocation-bar [data-band="staked"]'
        )
        self.wait_until(lambda: segment.get_attribute("aria-pressed") == "true")

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_subtotals_still_add_up_after_filtering(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The money column's whole promise, under a filter.

        Hiding a category has to take its positions out of every subtotal above
        them, or the reader is shown venue figures that no longer sum to the
        asset header they sit under -- which is worse than not filtering at all.

        Read through `_group_figure`, because a group does not always show a
        subtotal: a group of one never renders one, and a filter that leaves one
        position visible makes the toolbar hide the one that is there. Both are
        the same rule -- a subtotal that would only repeat the row below it is
        not shown -- and in both the group's figure is on that row.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        self.press('.figs .fig[data-band="defi"]')
        self.open_assets()

        checked = 0
        for card in self.browser.find_elements(By.CSS_SELECTOR, "#asset-list > .fitem"):
            if not card.is_displayed():
                continue
            groups = [
                group
                for group in card.find_elements(By.CSS_SELECTOR, ".pgroup")
                if group.is_displayed()
            ]
            if not groups:
                continue
            header = self._number(card.find_element(By.CSS_SELECTOR, ".cval .val").text)
            summed = sum(self._group_figure(group) for group in groups)
            with self.subTest(asset=card.get_attribute("id")):
                self.assertAlmostEqual(header, summed, delta=0.02)
            checked += 1

        self.assertGreater(checked, 3, "too few assets survived the filter to prove it")

    def _group_figure(self, group):
        """Return the figure a `.pgroup` is currently showing.

        Read off the rendered text rather than `data-val`, because what is
        under test is what the toolbar recomputed and painted, not what the
        server sent. When the subtotal is hidden -- one visible position, so it
        would only repeat the row -- that row is the group's figure.
        """
        totals = [
            cell
            for cell in group.find_elements(By.CSS_SELECTOR, ".pgroup-total")
            if cell.is_displayed()
        ]
        if totals:
            return self._number(totals[0].text)
        rows = [
            cell
            for cell in group.find_elements(
                By.CSS_SELECTOR, ".position > .position-row > .position-val > .amt"
            )
            if cell.is_displayed()
        ]
        self.assertEqual(
            1,
            len(rows),
            "a group showing no subtotal has more than one position visible",
        )
        return self._number(rows[0].text)

    @staticmethod
    def _number(text):
        """Read a rendered figure back as a number.

        Parentheses are how this design writes a negative, and there are five on
        the reference address -- reading them as positive would make a filtered
        subtotal appear not to add up when it does.
        """
        cleaned = text.split()[0].replace(",", "")
        if cleaned.startswith("(") and cleaned.endswith(")"):
            return -float(cleaned[1:-1])
        return float(cleaned)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_sorting_reorders_the_list_and_reverses(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        self.press('#tb-sort [data-sort="name"]')
        self.wait_until(lambda: self.shown() != [])
        descending = self._names()

        self.press("#tb-dir")
        self.wait_until(lambda: self._names() != descending)
        ascending = self._names()

        self.assertEqual(sorted(descending, reverse=True), descending)
        self.assertEqual(sorted(ascending), ascending)
        # Not `reversed(descending)`: the load-more rule keeps a *count* of rows
        # and applies it to the display order -- `utils/cutoff.py` is explicit
        # that it does not reorder -- so the two directions legitimately show
        # different rows. What has to hold is that each is ordered its own way,
        # and that the ends of the alphabet swapped.
        self.assertLess(ascending[0], descending[0])

    def _names(self):
        return [
            row.get_attribute("data-sort-name")
            for row in self.browser.find_elements(By.CSS_SELECTOR, "#asset-list > .fitem")
            if row.is_displayed()
        ]

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_pinned_row_survives_a_sort(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The reason sorting does not touch the DOM itself.

        Sorting and pinning both decide what order the rows are in. If the
        toolbar reordered directly, whichever ran last would undo the other --
        so it hands `pins.js` a new baseline and pinning still wins, which is
        right: a pin is the reader saying "this one, whatever else is going on".
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        # Something well down the list, so a sort would move it if it could.
        rows = self.shown()
        target = rows[len(rows) // 2]
        self.browser.find_element(By.CSS_SELECTOR, f'#{target} [data-pin]').click()
        self.wait_until(lambda: self.shown()[0] == target)

        self.press('#tb-sort [data-sort="name"]')

        self.wait_until(lambda: self.shown()[0] == target)
        self.assertEqual(
            target, self.shown()[0], "a sort threw away what the reader had pinned"
        )
        # And the rest is genuinely sorted underneath it.
        rest = self._names()[1:]
        self.assertEqual(sorted(rest, reverse=True), rest)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_each_section_shows_a_first_batch_and_offers_the_next(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The load-more rule, replacing the prototype's 95/99/99.5/All.

        That control was a way to *demonstrate* the page with everything on
        screen before a load-more existed. What a reader wants is a first
        screen that is a sensible size and a way to ask for more, which is a
        count -- not a share of the value.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        first = len(self.shown())
        section = self.browser.find_element(By.CSS_SELECTOR, ".dynamic-page .asasec")
        batch = int(section.get_attribute("data-initial"))
        self.assertEqual(batch, first, "the first screen is not the published batch")

        control = self.browser.find_element(
            By.CSS_SELECTOR, ".dynamic-page .asasec [data-show-more]"
        )
        self.assertIn(str(batch), control.text)
        control.click()

        self.wait_until(lambda: len(self.shown()) > first)
        self.assertEqual(first + batch, len(self.shown()))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_collections_have_their_own_smaller_batch(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Fewer, and taller, so a smaller first screen holds the same page."""
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        assets = self.browser.find_element(By.CSS_SELECTOR, ".dynamic-page .asasec")
        collections = self.browser.find_element(By.CSS_SELECTOR, ".dynamic-page .nftsec")
        smaller = int(collections.get_attribute("data-initial"))

        self.assertLess(smaller, int(assets.get_attribute("data-initial")))
        self.assertEqual(smaller, len(self.shown("#nft-list > .fitem")))

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_grouping_by_venue_moves_the_rows_and_gives_them_back(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Moved, not copied -- and the return trip is exact.

        A copy would put a second element on the page with the same `data-pid`,
        and a pin names a position by that id. The return trip is the half that
        broke: it remembered each group's next sibling, and an asset holding
        four venues had all four moved away.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        before = self._group_order()
        positions = len(self.browser.find_elements(By.CSS_SELECTOR, ".position"))

        self.press('#tb-group [data-group="venue"]')

        self.wait_until(lambda: self.shown("#venue-list > .fitem") != [])
        self.assertTrue(self.browser.find_element(By.ID, "asset-list").get_attribute("hidden"))
        self.assertEqual(
            positions,
            len(self.browser.find_elements(By.CSS_SELECTOR, ".position")),
            "grouping by venue duplicated or dropped position rows",
        )
        # The section says what it is showing, rather than still saying Assets.
        # Compared case-insensitively: `.eyebrow` upper-cases it in CSS, and
        # `.text` reports what the reader sees, not what the script wrote.
        self.assertEqual(
            "venues",
            self.browser.find_element(
                By.CSS_SELECTOR, ".asasec .section-head h2"
            ).text.lower(),
        )

        self.press('#tb-group [data-group="asset"]')

        self.wait_until(lambda: self.shown() != [])
        self.assertEqual(before, self._group_order(), "a group came back in the wrong place")
        self.assertEqual([], self.javascript_errors())

    def _group_order(self):
        return self.browser.execute_script(
            "return Array.prototype.map.call("
            "  document.querySelectorAll('#asset-list .pgroup'),"
            "  function (g) {"
            "    return g.closest('.fitem').id + ':' + g.getAttribute('data-venue');"
            "  });"
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_venue_card_names_its_groups_by_asset(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Otherwise the card is a column of identical headings.

        Under its asset a group is named by its venue; inside a venue card it
        has to be named by its asset, or "Wallet balance" appears thirty-eight
        times with no way to tell which holding each one is.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        self.press('#tb-group [data-group="venue"]')
        self.wait_until(lambda: self.shown("#venue-list > .fitem") != [])

        card = self.browser.find_element(By.CSS_SELECTOR, "#venue-list > .fitem")
        headings = [
            group.find_element(By.CSS_SELECTOR, ".pgroup-name").text.strip()
            for group in card.find_elements(By.CSS_SELECTOR, ".pgroup")
        ][:6]
        self.assertGreater(len(headings), 1, "one group proves no naming")
        self.assertEqual(
            len(headings),
            len(set(headings)),
            f"the venue card repeats a heading: {headings}",
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_reset_puts_the_page_back(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        served = self.shown()

        self.filter_for("algo")
        self.press('#tb-ccy [data-ccy="USD"]')
        self.press('#tb-group [data-group="venue"]')
        self.press('.figs .fig[data-band="nft"]')
        self.wait_until(
            lambda: not self.browser.find_element(By.ID, "tb-reset").get_attribute("disabled")
        )

        self.press("#tb-reset")

        self.wait_until(lambda: self.shown() == served)
        self.assertEqual("", self.browser.find_element(By.ID, "tb-q").get_attribute("value"))
        self.assertTrue(self.browser.find_element(By.ID, "tb-reset").get_attribute("disabled"))
        self.assertEqual("", self.status())
        self.assertTrue(
            self.browser.find_element(By.CSS_SELECTOR, ".dynamic-page .nftsec").is_displayed()
        )
        self.assertEqual([], self.javascript_errors())

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_view_survives_a_reload(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Kept in the reader's browser, because the page cannot keep it.

        This page's cache entry is shared by every reader on the layout, so the
        server must not know what this one has filtered to -- which makes the
        round trip the only thing that can show the state was really stored.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()
        self.press('#tb-ccy [data-ccy="USD"]')
        self.press('#tb-sort [data-sort="name"]')
        expected = self._names()

        self.open_page()

        self.wait_until(lambda: self._names() == expected)
        self.assertEqual(
            "true",
            self.browser.find_element(
                By.CSS_SELECTOR, '#tb-ccy [data-ccy="USD"]'
            ).get_attribute("aria-pressed"),
        )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_the_toolbar_stays_reachable_while_reading(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """Its whole purpose is to change what is below it.

        A reader scrolled to a row two hundred deep cannot use a control that
        scrolled away four screens ago.
        """
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}
        self.sign_in()
        self.open_page()

        self.browser.execute_script("window.scrollTo(0, 2000);")
        self.wait_until(lambda: self.browser.execute_script("return window.scrollY;") > 500)

        toolbar = self.browser.find_element(By.ID, "toolbar")
        top = self.browser.execute_script(
            "return arguments[0].getBoundingClientRect().top;", toolbar
        )
        self.assertGreaterEqual(top, -1, "the toolbar scrolled off the top of the screen")
        self.assertLess(top, 200, f"the toolbar is not where a reader left it: {top}")
