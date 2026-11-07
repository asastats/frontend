"""Functional tests for the app's safe area: the strips the system bars cover.

Chrome is told the insets of an iPhone with a Dynamic Island through CDP, so
`env(safe-area-inset-*)` resolves as it does in the app's WebView.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest
from .test_app_client import APP_USER_AGENT

TOP = 59
BOTTOM = 34

STRIP = """
var style = getComputedStyle(document.body, arguments[0]);
return {position: style.position, height: parseFloat(style.height),
        background: style.backgroundColor};
"""
RECT = "return document.querySelector(arguments[0]).getBoundingClientRect().toJSON();"
LONG_PAGE = "document.body.style.minHeight = '9000px';"


class SafeAreaTestCase(FunctionalTest):
    def setUp(self):
        super().setUp()
        self.browser.execute_cdp_cmd(
            "Emulation.setSafeAreaInsetsOverride",
            {"insets": {"top": TOP, "bottom": BOTTOM, "left": 0, "right": 0}},
        )

    def _open(self, path):
        self.browser.get(self.server_url + path)

    def _style(self, selector, name):
        return self.browser.execute_script(
            "return getComputedStyle(document.querySelector(arguments[0]))"
            ".getPropertyValue(arguments[1]);",
            selector,
            name,
        )

    def _scroll(self, y=800):
        self.browser.execute_script(f"window.scrollTo({{top: {y}, behavior: 'instant'}});")
        self.wait_until(lambda: self.browser.execute_script("return scrollY;") > 0)

    def _insert(self, html):
        self.browser.execute_script(
            "document.body.insertAdjacentHTML('afterbegin', arguments[0]);", html
        )


class AppSafeAreaEveryPageTest(SafeAreaTestCase):
    """Each kind of page leaves the bars' strips clear and paints them."""

    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def _assert_safe_area(self, path, top_colour, bottom_colour, page_padding=0):
        self._open(path)
        self.assertEqual(
            self._style("body", "padding-top"), f"{TOP + page_padding}px"
        )
        self.assertEqual(
            self._style("body", "padding-bottom"), f"{BOTTOM + page_padding}px"
        )

        top = self.browser.execute_script(STRIP, "::before")
        bottom = self.browser.execute_script(STRIP, "::after")

        self.assertEqual((top["position"], top["height"]), ("fixed", TOP))
        self.assertEqual((bottom["position"], bottom["height"]), ("fixed", BOTTOM))
        for strip in (top, bottom):
            self.assertNotEqual(strip["background"], "rgba(0, 0, 0, 0)")
        self.assertEqual(top["background"], self._style(*top_colour))
        self.assertEqual(bottom["background"], self._style(*bottom_colour))

    def test_page_with_the_site_header_takes_the_header_and_footer_colours(self):
        self._assert_safe_area(
            reverse("faq"),
            ("body > header", "background-color"),
            ("body > footer", "background-color"),
        )

    def test_terms_page_takes_the_header_and_footer_colours(self):
        self._assert_safe_area(
            reverse("terms"),
            ("body > header", "background-color"),
            ("body > footer", "background-color"),
        )

    def test_signup_links_open_in_place_on_pages_with_the_safe_area(self):
        for text, name in (("Terms of use", "terms"), ("Privacy Policy", "asm_privacy")):
            with self.subTest(link=text):
                self._open(reverse("account_signup"))

                link = self.browser.find_element(By.LINK_TEXT, text)
                # A reader scrolls it out from behind the bottom strip; Selenium does not.
                self.browser.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});",
                    link,
                )
                link.click()

                self.wait_until(
                    lambda: self.browser.current_url
                    == self.server_url + reverse(name)
                )
                self.assertEqual(len(self.browser.window_handles), 1)
                self.assertEqual(self._style("body", "padding-top"), f"{TOP}px")
                # The site's own header is the way on from here on iOS.
                self.browser.find_element(By.CSS_SELECTOR, "body > header a[href='/']")

                self.browser.back()

                self.wait_until(
                    lambda: self.browser.current_url
                    == self.server_url + reverse("account_signup")
                )

    def test_start_page_without_a_header_takes_the_body_colour(self):
        self._assert_safe_area(
            reverse("index"),
            ("body", "background-color"),
            ("body > footer", "background-color"),
        )

    def test_error_page_takes_the_body_colour(self):
        self._assert_safe_area(
            "/no/such/page/",
            ("body", "background-color"),
            ("body", "background-color"),
            page_padding=24,
        )

    def test_api_pages_take_the_body_colour(self):
        for name in ("swagger-ui", "redoc"):
            with self.subTest(page=name):
                self._assert_safe_area(
                    reverse(name),
                    ("body", "background-color"),
                    ("body", "background-color"),
                )

    def test_api_pages_load_app_js_for_the_status_bar(self):
        for name in ("swagger-ui", "redoc"):
            with self.subTest(page=name):
                self._open(reverse(name))
                self.wait_until(
                    lambda: self.browser.execute_script("return !!window.ASAStatsApp;")
                )

    def test_strips_follow_a_theme_change(self):
        self._open(reverse("faq"))
        before = self.browser.execute_script(STRIP, "::before")["background"]

        self.browser.execute_script(
            "document.documentElement.setAttribute('data-theme', 'aqua');"
        )

        strip = self.browser.execute_script(STRIP, "::before")["background"]
        self.assertNotEqual(strip, before)
        self.assertEqual(strip, self._style("body > header", "background-color"))

    def test_scrolled_content_does_not_show_in_the_top_strip(self):
        self._open(reverse("faq"))
        self.browser.execute_script(LONG_PAGE)
        self._scroll()

        # A pseudo-element hit-tests as its element: anything else is on top of it.
        hit = self.browser.execute_script(
            "return document.elementFromPoint(innerWidth / 2, arguments[0]).tagName;",
            TOP // 2,
        )
        self.assertEqual(hit, "BODY")

    def test_anchor_jump_lands_below_the_top_strip(self):
        self._open(reverse("disclaimer"))
        # Long enough that the anchor can reach the top of the screen.
        self.browser.execute_script(LONG_PAGE)
        self.browser.execute_script("location.hash = '#warranty';")
        self.wait_until(lambda: self.browser.execute_script("return scrollY;") > 0)

        rect = self.browser.execute_script(RECT, "#warranty")
        self.assertGreaterEqual(rect["top"], TOP)

    def test_sticky_toolbar_stops_below_the_top_strip(self):
        self._open(reverse("faq"))
        self._insert('<div class="dynamic-page"><div class="toolbar">x</div></div>')
        self.browser.execute_script(
            "document.querySelector('.dynamic-page').style.minHeight = '5000px';"
        )
        self._scroll()

        rect = self.browser.execute_script(RECT, ".dynamic-page .toolbar")
        self.assertEqual(rect["top"], TOP)

    def test_fixed_controls_stay_above_the_bottom_strip(self):
        self._open(reverse("faq"))
        self._insert(
            '<a id="scroll-to-top" class="fixed bottom-6 right-6">x</a>'
            '<div id="notice" class="alert fixed bottom-4">x</div>'
            '<div class="toast toast-bottom"><div>x</div></div>'
        )
        height = self.browser.execute_script("return innerHeight;")

        for selector in ("#scroll-to-top", "#notice", ".toast"):
            with self.subTest(selector=selector):
                rect = self.browser.execute_script(RECT, selector)
                self.assertLessEqual(rect["bottom"], height - BOTTOM)

    def test_scroll_to_top_clears_a_landscape_notch(self):
        self.browser.execute_cdp_cmd(
            "Emulation.setSafeAreaInsetsOverride",
            {"insets": {"top": 0, "bottom": 21, "left": 0, "right": 59}},
        )
        self._open(reverse("faq"))
        self._insert('<a id="scroll-to-top" class="fixed bottom-6 right-6">x</a>')

        rect = self.browser.execute_script(RECT, "#scroll-to-top")
        width = self.browser.execute_script("return innerWidth;")
        self.assertLessEqual(rect["right"], width - 59)

    def test_tall_dialogs_stay_between_the_strips(self):
        self.browser.set_window_size(600, 844)
        self._open(reverse("faq"))
        height = self.browser.execute_script("return innerHeight;")

        for name in ("", "swap-modal", "dustsweep-modal", "alerts-modal"):
            with self.subTest(dialog=name):
                self._insert(
                    f'<dialog id="tall-{name}" class="{name}">'
                    '<div style="height: 5000px">x</div></dialog>'
                )
                self.browser.execute_script(
                    "document.getElementById(arguments[0]).showModal();",
                    f"tall-{name}",
                )

                rect = self.browser.execute_script(RECT, f"#tall-{name}")
                self.assertGreaterEqual(rect["top"], TOP)
                self.assertLessEqual(rect["bottom"], height - BOTTOM)

                self.browser.execute_script(
                    "document.getElementById(arguments[0]).close();",
                    f"tall-{name}",
                )


class ApiBackLinkMixin:
    """Each API page, with the element that shows it has finished drawing."""

    PAGES = (("swagger-ui", ".opblock"), ("redoc", ".menu-content"))

    def _open_api_page_from_faq(self, name, drawn):
        self._open(reverse("faq"))
        self._insert(f'<a id="to-api" href="{reverse(name)}">x</a>')
        self.browser.find_element(By.ID, "to-api").click()
        self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, drawn), timeout=20
        )

    def _assert_back_is_tappable(self, top):
        rect = self.browser.execute_script(RECT, "#api-back")
        self.assertEqual(rect["top"], top)
        hit = self.browser.execute_script(
            "return document.elementFromPoint(arguments[0], arguments[1]).id;",
            rect["left"] + rect["width"] / 2,
            rect["top"] + rect["height"] / 2,
        )
        self.assertEqual(hit, "api-back")

        self.browser.find_element(By.ID, "api-back").click()

        self.wait_until(
            lambda: self.browser.current_url == self.server_url + reverse("faq")
        )

    def _assert_back_clear_of_redoc_menu(self):
        self.browser.set_window_size(1200, 844)
        self._open(reverse("redoc"))
        self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, ".menu-content"),
            timeout=20,
        )
        self._scroll()

        back = self.browser.execute_script(RECT, "#api-back")
        menu = self.browser.execute_script(RECT, ".menu-content")
        self.assertGreaterEqual(menu["top"], back["bottom"])


class AppApiBackLinkTest(ApiBackLinkMixin, SafeAreaTestCase):
    """The report: the Back link on the API page could not be tapped."""

    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def test_page_is_laid_out_under_the_bars(self):
        for name, drawn in self.PAGES:
            with self.subTest(page=name):
                self._open_api_page_from_faq(name, drawn)
                viewport = self.browser.execute_script(
                    "var metas = document.querySelectorAll('meta[name=viewport]');"
                    "return metas[metas.length - 1].content;"
                )
                self.assertIn("viewport-fit=cover", viewport)

    def test_back_link_is_tappable_when_the_page_opens(self):
        for name, drawn in self.PAGES:
            with self.subTest(page=name):
                self._open_api_page_from_faq(name, drawn)

                self._assert_back_is_tappable(TOP)

    def test_back_link_is_tappable_after_scrolling(self):
        for name, drawn in self.PAGES:
            with self.subTest(page=name):
                self._open_api_page_from_faq(name, drawn)
                self._scroll()

                self._assert_back_is_tappable(TOP)

    def test_back_link_does_not_cover_the_redoc_menu(self):
        self._assert_back_clear_of_redoc_menu()

    def test_redoc_phone_menu_opens_below_the_back_link(self):
        self.browser.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": False},
        )
        self._open(reverse("redoc"))
        self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, ".menu-content"),
            timeout=20,
        )
        # Redoc's own floating button; its class names are generated.
        self.browser.execute_script(
            "document.elementFromPoint(324, 770).closest('div').click();"
        )
        self.wait_until(
            lambda: self.browser.execute_script(RECT, ".menu-content")["height"] > 0
        )
        self.wait_until(
            lambda: self.browser.execute_script(RECT, ".menu-content")["top"]
            == self.browser.execute_script(RECT, "#api-back")["bottom"],
        )

        hit = self.browser.execute_script(
            "return document.elementFromPoint(100, arguments[0]).id;", TOP + 24
        )
        self.assertEqual(hit, "api-back")

    def test_scrolled_redoc_does_not_show_in_the_top_strip(self):
        self._open(reverse("redoc"))
        self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, ".menu-content"),
            timeout=20,
        )
        self._scroll()

        hit = self.browser.execute_script(
            "return document.elementFromPoint(innerWidth / 2, arguments[0]).tagName;",
            TOP // 2,
        )
        self.assertEqual(hit, "BODY")


class BrowserSafeAreaTest(ApiBackLinkMixin, SafeAreaTestCase):
    """A browser on a phone with the same insets gets the plain website."""

    def test_browser_pages_have_no_safe_area(self):
        for path in (reverse("faq"), reverse("swagger-ui"), reverse("redoc"), "/no/such/"):
            with self.subTest(path=path):
                self._open(path)
                html = self.browser.page_source
                self.assertNotIn("viewport-fit", html)
                self.assertNotIn("safe-area-inset", html)
                self.assertEqual(
                    self.browser.execute_script(STRIP, "::before")["position"],
                    "static",
                )

    def test_browser_api_back_link_sits_at_the_top(self):
        for name, drawn in self.PAGES:
            with self.subTest(page=name):
                self._open_api_page_from_faq(name, drawn)

                self._assert_back_is_tappable(0)

    def test_browser_api_back_link_stays_in_view_while_scrolling(self):
        for name, drawn in self.PAGES:
            with self.subTest(page=name):
                self._open_api_page_from_faq(name, drawn)
                self._scroll()

                self._assert_back_is_tappable(0)

    def test_browser_back_link_does_not_cover_the_redoc_menu(self):
        self._assert_back_clear_of_redoc_menu()

    def test_browser_redoc_in_a_new_tab_goes_back_to_the_start_page(self):
        self._open(reverse("faq"))
        self._insert(
            f'<a id="to-api" href="{reverse("redoc")}" target="_blank" rel="noopener">x</a>'
        )
        self.browser.find_element(By.ID, "to-api").click()
        self.wait_until(lambda: len(self.browser.window_handles) == 2)
        self.browser.switch_to.window(self.browser.window_handles[-1])
        self.wait_until(
            lambda: self.browser.find_elements(By.CSS_SELECTOR, ".menu-content"),
            timeout=20,
        )

        self.browser.find_element(By.ID, "api-back").click()

        self.wait_until(
            lambda: self.browser.current_url == self.server_url + reverse("index")
        )
