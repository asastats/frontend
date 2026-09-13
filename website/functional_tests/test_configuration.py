from utils.helpers import load_transparency_reports

from .base import FunctionalTest

SITEMAP_URLS = (
    "about",
    "tokenomics",
    "faq",
    "features",
    "subscriptions",
    "disclaimer",
    "asm-privacy",
    "accounts/signup",
    "accounts/login",
    "accounts/password/reset",
)
SITEMAP_FILES = ("whitepaper.pdf",)


class ConfigurationTest(FunctionalTest):
    def test_auth_privacy_file(self):
        self.browser.get(self.server_url + "/static/auth_privacy.html")
        self.assertIn("<h1>Privacy policy</h1>", self.browser.page_source)

    def test_auth_terms_file(self):
        self.browser.get(self.server_url + "/static/auth_terms.html")
        self.assertIn("<h1>Terms of use</h1>", self.browser.page_source)

    def test_sitemap_urls(self):
        self.browser.get(self.server_url + "/sitemap.xml")
        for url in SITEMAP_URLS:
            self.assertIn("/{}/".format(url), self.browser.page_source)

    def test_transparency_report_files(self):
        self.browser.get(self.server_url + "/sitemap.xml")

        for year_group in load_transparency_reports():
            for report in year_group["months"]:
                expected_url = (
                    f"/transparency-report-{report['year']}-{report['month']}.pdf"
                )
                self.assertIn(
                    expected_url,
                    self.browser.page_source,
                )
                print(expected_url)

    def test_sitemap_files(self):
        self.browser.get(self.server_url + "/sitemap.xml")

        for url in SITEMAP_FILES:
            self.assertIn("/{}".format(url), self.browser.page_source)


class PageLoadTimeoutTest(FunctionalTest):
    """The harness's own guard against a stalled page taking a test with it.

    **The bug this pins was never a chromedriver crash**, though it read as
    one. chromedriver waits 300 s by default for a page to fire `load`;
    selenium waits 120 s for chromedriver to answer. A page that stalls between
    those two numbers blows selenium's clock first and surfaces as::

        urllib3.exceptions.ReadTimeoutError: HTTPConnectionPool(
            host='localhost', port=41749): Read timed out. (read timeout=120)

    which names chromedriver's own port and looks like the driver died. It had
    not: it was waiting, as told. Two CI runs and a local reproduction at about
    one in twenty all had that shape, always in a `browser.get`, always with
    healthy neighbours either side.

    One stalled subresource is enough to cause it - Chrome's `load` waits for
    every image - which is why it struck pages with the most on them and never
    reproduced on a quiet one.
    """

    def _black_hole(self):
        """Return the URL of a socket that accepts and never answers."""
        import socket
        import threading

        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(8)
        held = []
        running = [True]

        def accept():
            while running[0]:
                try:
                    connection, _ = listener.accept()
                    held.append(connection)  # never answered, never closed
                except OSError:
                    return

        threading.Thread(target=accept, daemon=True).start()

        def stop():
            running[0] = False
            for connection in held:
                connection.close()
            listener.close()

        self.addCleanup(stop)
        return f"http://127.0.0.1:{listener.getsockname()[1]}/"

    def test_a_stalled_page_fails_as_a_timeout_and_leaves_the_session_usable(self):
        """Asserted on behaviour rather than on the setting.

        Reading `PAGE_LOAD_TIMEOUT` back would pass just as happily if nothing
        ever applied it, and applying it is the part that was missing.
        """
        import time

        from selenium.common.exceptions import TimeoutException

        started = time.time()
        with self.assertRaises(TimeoutException):
            self.browser.get(self._black_hole())
        elapsed = time.time() - started

        assert elapsed < 120, (
            f"a stalled page took {elapsed:.0f}s; under selenium's own 120s "
            "timeout is the whole point, or the failure goes back to naming "
            "chromedriver's port instead of the page"
        )
        # The session survives, which it does not when selenium's clock expires
        # mid-command: every later call in that test fails too.
        self.browser.get(self.server_url + "/404.html")
