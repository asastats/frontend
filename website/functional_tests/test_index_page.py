from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium.webdriver.common.by import By

from core.models import BundleName

from .base import TESTING_ADDRESS, FunctionalTest


class IndexPageTest(FunctionalTest):
    def test_index_page_has_track_button_that_leads_to_address_page(self):
        self.browser.get(self.server_url)

        self.assertIn("ASA Stats", self.browser.title)

        address = self.find_elem_by_id("id_address")
        address.clear()
        address.send_keys(TESTING_ADDRESS)

        button = self.find_elem_by_id("track")
        # Materialize upper-cased button text in CSS; DaisyUI does not, so the
        # rendered casing is now a design choice rather than content.
        self.assertEqual(button.text.strip().lower(), "track")

        with self.wait_for_page_load(timeout=2):
            self.find_elem_by_id("track").click()
        self.assertIn(TESTING_ADDRESS, self.browser.current_url)


class IndexPageContentTest(FunctionalTest):
    """What the landing page shows before anyone searches."""

    def test_the_search_field_and_button_are_present(self):
        self.browser.get(self.server_url + reverse("index"))
        self.assertTrue(self.find_elem_by_id("id_address").is_displayed())
        button = self.find_elem_by_id("track")
        self.assertEqual(button.text.strip().lower(), "track")

    def test_a_logged_in_viewer_sees_their_bundles(self):
        email = "bundles@example.com"
        self.create_cookie_and_go_to_index_page_tier(email, permission=100)
        user = get_user_model().objects.get(username=email)
        # profile.bundlenames is a read-only property over a query, so the row
        # is created directly rather than through a related manager.
        BundleName.objects.create(
            profile=user.profile,
            name="my-bundle",
            addresses=TESTING_ADDRESS,
            bundle="A" * 40,
        )

        self.browser.get(self.server_url + reverse("index"))
        self.assertIn("my-bundle", self.browser.page_source)
        self.assertTrue(
            self.browser.find_elements(By.CSS_SELECTOR, "a[href*='my-bundle']")
        )


class IndexSloganTest(FunctionalTest):
    """The slogan must be readable whole, at every width.

    Eleven slogans of 41 to 80 characters share one `<h1>`, and it used to
    carry Tailwind's `truncate` - so the long ones lost their ending to an
    ellipsis on a desktop as well as a phone. Nothing in a unit test can see
    that: the template renders the whole string either way, and only a browser
    laying it out knows what the reader is left with.
    """

    #: the longest of the eleven, and the only one whose fit was ever in doubt
    LONGEST = (
        "The maximum value of your assets aggregated using the entire "
        "ecosystem liquidity"
    )

    def _open_with_longest_slogan(self, width, height=900):
        from unittest import mock

        self.browser.set_window_size(width, height)
        with mock.patch("core.views.random_slogan", return_value=self.LONGEST):
            self.browser.get(self.server_url + reverse("index"))
        return self.find_elem_by_css(".index-slogan")

    def _metrics(self, element):
        return self.browser.execute_script(
            "const e = arguments[0], s = getComputedStyle(e);"
            "return {"
            "  clipped: e.scrollWidth > e.clientWidth + 1,"
            "  lines: Math.round(e.getBoundingClientRect().height"
            "         / parseFloat(s.lineHeight)),"
            "  size: parseFloat(s.fontSize),"
            "  overflow: s.textOverflow"
            "};",
            element,
        )

    def test_the_whole_slogan_is_rendered(self):
        """The text is all there even when the layout hides some of it."""
        slogan = self._open_with_longest_slogan(1280)

        assert slogan.get_attribute("textContent").strip() == self.LONGEST

    def test_the_longest_slogan_is_never_clipped(self):
        """The actual bug: an ellipsis ate the end of the sentence.

        Asserted at three widths, because it was cut on a wide screen too -
        the container stops growing at 672px, so a desktop was no safer than a
        phone once the font size was too large for eighty characters.
        """
        for width in (1280, 768, 375):
            metrics = self._metrics(self._open_with_longest_slogan(width))

            assert metrics["clipped"] is False, f"clipped at {width}px"
            assert metrics["overflow"] != "ellipsis", f"ellipsis at {width}px"

    def test_the_longest_slogan_holds_one_line_where_it_can(self):
        """Wrapping is the fallback, not the plan, and only a phone needs it."""
        for width in (1280, 768):
            metrics = self._metrics(self._open_with_longest_slogan(width))

            assert metrics["lines"] == 1, f"{metrics['lines']} lines at {width}px"

    def test_a_phone_shrinks_the_font_rather_than_hiding_words(self):
        """No font size holds eighty characters on one phone line and stays
        readable, so it wraps - but it shrinks first, and it keeps every word.
        """
        narrow = self._metrics(self._open_with_longest_slogan(375))
        wide = self._metrics(self._open_with_longest_slogan(1280))

        assert narrow["size"] < wide["size"]
        assert narrow["size"] >= 15, "shrunk past legibility"
        assert narrow["clipped"] is False

    def test_a_short_slogan_still_fits_on_one_line_on_a_phone(self):
        """The floor must not be so low that it wraps what never needed to."""
        from unittest import mock

        shortest = "All your Algorand assets on one dashboard"
        self.browser.set_window_size(375, 900)
        with mock.patch("core.views.random_slogan", return_value=shortest):
            self.browser.get(self.server_url + reverse("index"))

        assert self._metrics(self.find_elem_by_css(".index-slogan"))["lines"] == 1
