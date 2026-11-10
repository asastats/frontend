"""Functional tests for pull down to refresh on the address page, in the app."""

from unittest import mock

from .base import FunctionalTest
from .test_address_page import ADDRESS, _sample_payload
from .test_app_client import APP_USER_AGENT

MARK = "window.pullRefreshMark = 'before';"
MARKED = "return window.pullRefreshMark === 'before';"
FIRST_SECTION = "document.querySelector('.asasec .fitem')"


class PullRefreshTestCase(FunctionalTest):
    def setUp(self):
        super().setUp()
        for target, value in (
            ("core.context_processors.fetch_capabilities", {"permission": 0}),
            ("core.views.check_export_status", {}),
            ("core.views.fetch_and_serialize_account", _sample_payload()),
        ):
            patcher = mock.patch(target, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _open(self):
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.browser.execute_script(MARK)

    def _pull(self, distance):
        """Drag one finger down from near the top of the page by `distance` px."""
        touch = lambda kind, y: self.browser.execute_cdp_cmd(  # noqa: E731
            "Input.dispatchTouchEvent",
            {"type": kind, "touchPoints": [] if kind == "touchEnd" else [{"x": 200, "y": y}]},
        )
        touch("touchStart", 150)
        for step in range(1, 11):
            touch("touchMove", 150 + distance * step / 10)
        touch("touchEnd", 0)

    def _reloaded(self):
        return not self.browser.execute_script(MARKED)


class AppPullRefreshTest(PullRefreshTestCase):
    def setup_platform(self):
        super().setup_platform()
        self.browser_options.add_argument(f"--user-agent={APP_USER_AGENT}")

    def test_a_long_pull_from_the_top_reloads_and_keeps_the_open_section(self):
        self._open()
        section = self.browser.execute_script(f"var s = {FIRST_SECTION}; s.open = true; return s.id;")

        self._pull(300)

        self.wait_until(self._reloaded)
        self.wait_until(
            lambda: self.browser.execute_script(f"return {FIRST_SECTION}.open;")
        )
        self.assertEqual(self.browser.execute_script(f"return {FIRST_SECTION}.id;"), section)

    def test_a_short_pull_does_not_reload(self):
        self._open()

        self._pull(60)

        self.sleep(1)
        self.assertFalse(self._reloaded())
        self.assertEqual(
            self.browser.execute_script(
                "return getComputedStyle(document.getElementById('pull-refresh')).opacity;"
            ),
            "0",
        )

    def test_a_pull_further_down_the_page_scrolls_instead(self):
        self._open()
        self.browser.execute_script(
            "document.body.style.minHeight = '9000px';"
            "window.scrollTo({top: 800, behavior: 'instant'});"
        )

        self._pull(300)

        self.sleep(1)
        self.assertFalse(self._reloaded())


class BrowserPullRefreshTest(PullRefreshTestCase):
    def test_a_browser_gets_no_pull_refresh(self):
        self._open()

        self.assertNotIn("pullrefresh.js", self.browser.page_source)
        self._pull(300)
        self.sleep(1)
        self.assertFalse(self._reloaded())
