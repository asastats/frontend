"""Functional tests for the address page's figure tooltips, in every layout.

The tooltip is DaisyUI's `::before` on the figure, and the asset cards are
`overflow: hidden`, so whether a reader sees it is a question of laid-out
geometry. See frontend/docs/logbook.md (2026-11-03).
"""

from unittest import mock

from django.contrib.auth import get_user_model
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from .base import FunctionalTest
from .test_address_dynamic_page import ASASTATSER, MoneyPageMixin, _sample_payload

#: (layout, first asset card, its header figure)
LAYOUTS = (
    ("classic", ".asasec details.fitem", "summary .val"),
    ("dynamic", "#asa-section .rows > details.fitem", ".cval .v"),
    ("dynamic-compact", "#asa-section .rows > details.fitem", ".cval .v"),
)

#: The tooltip's box in viewport coordinates: its offsets inside the figure,
#: moved by its transform, which is how DaisyUI places it.
TIP_RECT = """
var el = arguments[0];
var tip = getComputedStyle(el, '::before');
var box = el.getBoundingClientRect();
var m = new DOMMatrixReadOnly(tip.transform === 'none' ? undefined : tip.transform);
var left = box.left + el.clientLeft + parseFloat(tip.left) + m.m41;
var top = box.top + el.clientTop + parseFloat(tip.top) + m.m42;
return {left: left, top: top, right: left + parseFloat(tip.width),
        bottom: top + parseFloat(tip.height), opacity: parseFloat(tip.opacity),
        display: tip.display};
"""

RECT = """
var r = arguments[0].getBoundingClientRect();
return {left: r.left, top: r.top, right: r.right, bottom: r.bottom};
"""


class AddressTooltipsTest(MoneyPageMixin, FunctionalTest):
    """A figure's tooltip shows, inside its card, unless the reader turned it off."""

    def _open(self, email, layout, show_tooltips=True):
        self.sign_in(email, ASASTATSER, layout)
        profile = get_user_model().objects.get(username=email).profile
        profile.show_tooltips = show_tooltips
        profile.save()
        self.open_address()

    def _header_figure(self, card_selector, figure_selector):
        """Return the first asset card, closed, and its header figure once tipped."""
        card = self.browser.find_element(By.CSS_SELECTOR, card_selector)
        self.browser.execute_script("arguments[0].open = false;", card)
        figure = card.find_element(By.CSS_SELECTOR, figure_selector)
        self.wait_until(
            lambda: "tooltip" in figure.get_attribute("class")
            and figure.get_attribute("data-tip"),
            timeout=10,
        )
        self.browser.execute_script(
            "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", card
        )
        return card, figure

    def _hover(self, figure):
        """Point at `figure` until it is hovered; the first move can be lost."""

        def pointed():
            ActionChains(self.browser).move_to_element(figure).perform()
            return self.browser.execute_script("return arguments[0].matches(':hover');", figure)

        self.wait_until(pointed)

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_card_header_tooltip_is_drawn_inside_its_card(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        """The screenshot in bugs/tooltip.png: the tip opened upwards, past the
        top of a card that clips its content, and was cut off."""
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}

        for index, (layout, card_selector, figure_selector) in enumerate(LAYOUTS):
            with self.subTest(layout=layout):
                self._open(f"tips-inside-{index}@example.com", layout)
                card, figure = self._header_figure(card_selector, figure_selector)

                self._hover(figure)
                self.wait_until(
                    lambda: self.browser.execute_script(TIP_RECT, figure)["opacity"]
                    == 1.0
                )

                tip = self.browser.execute_script(TIP_RECT, figure)
                bounds = self.browser.execute_script(RECT, card)
                for edge in ("left", "top"):
                    self.assertGreaterEqual(
                        tip[edge], bounds[edge], f"{layout}: tip cut off at the {edge}"
                    )
                for edge in ("right", "bottom"):
                    self.assertLessEqual(
                        tip[edge], bounds[edge], f"{layout}: tip cut off at the {edge}"
                    )

    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_a_reader_who_turned_tooltips_off_sees_none(
        self, mocked_fetch, mocked_status, mocked_capabilities
    ):
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_capabilities.return_value = {"permission": ASASTATSER}

        for index, (layout, card_selector, figure_selector) in enumerate(LAYOUTS):
            with self.subTest(layout=layout):
                self._open(f"tips-off-{index}@example.com", layout, show_tooltips=False)
                _, figure = self._header_figure(card_selector, figure_selector)

                self._hover(figure)
                self.sleep(0.5)  # past DaisyUI's 75ms delay and 200ms fade

                self.assertEqual(
                    "none", self.browser.execute_script(TIP_RECT, figure)["display"]
                )
