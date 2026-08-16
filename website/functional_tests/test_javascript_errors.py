"""No page may throw while it loads.

An uncaught exception in a page script is not a local failure. jQuery runs
every ``$(fn)`` callback off one Deferred, and a callback that throws abandons
the rest of the queue -- so one broken line in a shared script silently
disables every page script registered after it, across the whole site.

That is exactly what the Materialize-to-DaisyUI migration produced twice, in
``mainSite``, which runs on every page:

* ``$('.sidenav').sidenav()`` -- a jQuery plugin installed by Materialize
  rather than a call on the ``M`` object, so the ``typeof M`` guards elsewhere
  in site.js did not cover it;
* ``isDark()`` reading ``document.getElementById("footer").dataset``, where
  ``#footer`` belongs to the Materialize base and is absent from the DaisyUI
  one.

Either way ``mainSite`` threw before its last line, so copy-to-clipboard and
the swap gate never bound -- and on the home page ``mainHome``, registered
after it, never ran at all: sorting and filtering were inert while the page
looked perfectly healthy. Nothing appeared in any log, and every other
assertion on those pages still passed.

Watching the console is the cheapest way to notice. These tests visit the
pages a signed-in and a signed-out visitor sees and fail on anything thrown.
"""

from utils.tests.fixtures import TEST_ADDRESS

from .base import FunctionalTest

#: Pages reachable without an account.
PUBLIC_PATHS = [
    "/",
    "/about/",
    "/tokenomics/",
    "/subscriptions/",
    "/faq/",
    "/features/",
    "/disclaimer/",
    "/sitemap/",
]

#: Pages reachable once signed in.
PRIVATE_PATHS = [
    "/home/",
    "/profile/",
    "/profile/edit",
    "/profile/add-bundle",
]


class JavaScriptErrorTest(FunctionalTest):
    """Testing class for uncaught browser exceptions during page load."""

    def _assert_clean(self, paths):
        """Visit each path in turn and fail naming the first page that threw.

        :param paths: site-relative urls to load
        :type paths: list
        """
        offenders = {}
        for path in paths:
            self.browser.get(self.server_url + path)
            self.wait_until(lambda: self.page_state()["ready"] == "complete")
            errors = self.javascript_errors()
            if errors:
                offenders[path] = errors
        self.assertEqual(
            offenders,
            {},
            "these pages threw while loading. A page script that throws takes "
            "every jQuery ready callback registered after it down with it, so "
            "the visible symptom is usually some unrelated control quietly "
            f"doing nothing:\n  {offenders}",
        )

    def test_public_pages_load_without_javascript_errors(self):
        self.record_javascript_errors()
        self.browser.get(self.server_url + "/")
        self.accept_cookie()
        self._assert_clean(PUBLIC_PATHS)

    def test_private_pages_load_without_javascript_errors(self):
        self.record_javascript_errors()
        self.create_cookie_and_go_to_bundlename_add_page(
            "jserrors@example.com", permission=258_885_438_200
        )
        self.accept_cookie()
        self.submit_bundlename_name("Bundle one", TEST_ADDRESS)
        self._assert_clean(PRIVATE_PATHS)
