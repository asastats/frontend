"""Functional tests for the pages moved onto the DaisyUI base template.

Two things are being checked here, and they are different in kind.

The first is the migration invariant: Materialize and the DaisyUI build both
define ``.btn``, ``.card``, ``.modal``, ``.badge``, ``.container`` and six more,
so a page that loaded both would have whichever lost the cascade silently
deform. Nothing in the templates enforces that a page picks exactly one -- a
stray ``{% extends 'base.html' %}`` would not fail any unit test -- so it is
asserted here, against the rendered page.

The second is that the behaviour on each converted page still works. These are
content pages, so "behaviour" is mostly links, anchors and the appearance
picker; the pages with real flows (index's search, export's tax states) get
their own cases.
"""

import logging
import traceback
from contextlib import contextmanager
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium.webdriver.common.by import By

from core.models import BundleName

from .base import TESTING_ADDRESS, FunctionalTest

#: Pages already moved onto base_tw.html, by URL name.
CONVERTED = [
    "index",
    "about",
    "asm_privacy",
    "faq",
    "features",
    "sitemap",
    "tokenomics",
    "subscriptions",
    "disclaimer",
]


@contextmanager
def captured_server_errors():
    """Collect what Django logs to ``django.request`` while the block runs.

    The live server runs in a thread of this process with ``DEBUG`` off, so a
    view that raises renders templates/500.html -- inline CSS, no stylesheet
    links, and no traceback anywhere the browser can see it. Without this the
    only symptom is "the page linked no stylesheet", which says nothing about
    why. The exception does reach this logger, so the assertion can carry it.
    """
    records = []
    handler = logging.Handler()
    handler.emit = records.append
    logger = logging.getLogger("django.request")
    logger.addHandler(handler)
    try:
        yield records
    finally:
        logger.removeHandler(handler)


def describe_errors(records):
    """Render captured log records, with tracebacks, for a failure message."""
    if not records:
        return ""
    out = ["", "  the server logged:"]
    for record in records:
        out.append(f"    {record.getMessage()}")
        if record.exc_info:
            for line in traceback.format_exception(*record.exc_info):
                out.extend("      " + part for part in line.rstrip().splitlines())
    return "\n".join(out)


class ConvertedPagesTest(FunctionalTest):
    """Every converted page renders on the new base, and only the new base."""

    # No backend mocking here, deliberately. functional_tests normally mocks the
    # engine (integration_tests/conftest.py takes the other route and starts it
    # on :8001), but every converted page is a content page that must render
    # with the engine unreachable -- which is exactly the state it is in during
    # these tests. Adding a mock would hide a page that cannot stand on its own.

    def _page_state(self):
        """Return {ready, sheets, title, text} for the current page in one call.

        One ``execute_script`` round trip rather than a Selenium query per
        element: every ``find_elements`` pays the implicit wait, and this runs
        over nine pages.
        """
        return self.browser.execute_script(
            "return {"
            "  ready: document.readyState,"
            "  sheets: Array.from("
            "    document.querySelectorAll('link[rel=\"stylesheet\"]')"
            "  ).map(function (l) { return l.getAttribute('href'); }),"
            "  title: document.title,"
            "  text: (document.body ? document.body.innerText : '').slice(0, 300)"
            "};"
        )

    def _visit(self, url):
        """Load ``url``, wait for it to settle, and describe what arrived.

        Returns the page state with an extra ``why`` string: everything a
        failure needs to name itself, including the server-side traceback.
        """
        with captured_server_errors() as errors:
            self.browser.get(url)
            self.wait_until(lambda: self._page_state()["ready"] == "complete")
            state = self._page_state()
        state["why"] = (
            f"\n  url:   {url}"
            f"\n  title: {state['title']!r}"
            f"\n  body:  {state['text']!r}" + describe_errors(errors)
        )
        return state

    def test_converted_pages_load_the_new_stylesheet_and_not_materialize(self):
        for name in CONVERTED:
            with self.subTest(page=name):
                state = self._visit(self.server_url + reverse(name))
                sheets = " ".join(state["sheets"])
                # templates/500.html carries inline CSS and links nothing, so
                # "no stylesheets" is how a server error looks from here.
                self.assertNotEqual(
                    state["title"],
                    "Internal server error",
                    f"{name} raised in the view{state['why']}",
                )
                self.assertTrue(
                    state["sheets"],
                    f"{name} linked no stylesheet at all{state['why']}",
                )
                self.assertIn(
                    "style.tw", sheets, f"{name} misses style.tw.css{state['why']}"
                )
                self.assertNotIn(
                    "materialize",
                    sheets,
                    f"{name} still loads Materialize{state['why']}",
                )
                # style.css is the Materialize-era sheet and goes with it.
                self.assertNotIn(
                    "style.min", sheets, f"{name} still loads style.min{state['why']}"
                )

    def test_a_page_still_on_the_old_base_keeps_materialize(self):
        """The other half of the invariant: the split is real, not accidental.

        If this ever fails it means every page has been converted, and both
        base templates can be collapsed into one.
        """
        state = self._visit(self.server_url + reverse("home"))
        sheets = " ".join(state["sheets"])
        self.assertIn("materialize", sheets, f"home lost Materialize{state['why']}")
        self.assertNotIn("style.tw", sheets, f"home gained style.tw{state['why']}")


class AppearancePickerTest(FunctionalTest):
    """The picker in base_tw.html, which replaces the old dark/light toggle."""

    def _open_picker(self):
        self.browser.get(self.server_url + reverse("disclaimer"))
        # A <details>, so it opens without scripting; open it directly rather
        # than clicking, which keeps the test about the choice, not the widget.
        self.browser.execute_script(
            "document.querySelector('#id-theme-list').closest('details').open = true;"
        )
        return self.browser.find_elements(
            By.CSS_SELECTOR, "#id-theme-list input[name='theme-dropdown']"
        )

    def test_picker_offers_exactly_the_themes_settings_declares(self):
        radios = self._open_picker()
        self.assertEqual(
            [r.get_attribute("value") for r in radios],
            list(settings.AVAILABLE_THEMES),
        )

    def test_no_theme_is_stamped_until_one_is_chosen(self):
        self.browser.get(self.server_url + reverse("disclaimer"))
        html = self.browser.find_element(By.TAG_NAME, "html")
        # Unstamped means DaisyUI's own default applies -- the `asastats` theme
        # is registered with `default: true`, so the page is still branded.
        self.assertIsNone(html.get_attribute("data-theme"))

    def test_choosing_a_theme_applies_it_and_survives_a_reload(self):
        radios = self._open_picker()
        target = next(r for r in radios if r.get_attribute("value") == "abyss")
        self.browser.execute_script(
            "arguments[0].checked = true;"
            "arguments[0].dispatchEvent(new Event('change'));",
            target,
        )
        self.wait_until(
            lambda: self.browser.find_element(By.TAG_NAME, "html").get_attribute(
                "data-theme"
            )
            == "abyss"
        )
        # The choice is client-side only, so it has to come back from storage.
        self.browser.get(self.server_url + reverse("faq"))
        self.wait_until(
            lambda: self.browser.find_element(By.TAG_NAME, "html").get_attribute(
                "data-theme"
            )
            == "abyss"
        )

    def test_the_picker_closes_once_a_theme_is_chosen(self):
        radios = self._open_picker()
        menu = self.browser.find_element(
            By.CSS_SELECTOR, "#id-theme-list"
        ).find_element(By.XPATH, "./ancestor::details")
        self.browser.execute_script(
            "arguments[0].dispatchEvent(new Event('change'));", radios[0]
        )
        self.wait_until(lambda: menu.get_attribute("open") is None)


class ContentPagesTest(FunctionalTest):
    """The prose pages: their structure carried over, not just their words."""

    def test_disclaimer_keeps_its_section_anchors(self):
        self.browser.get(self.server_url + reverse("disclaimer"))
        # These are linkable and appear in the sitemap and external references,
        # so the conversion had to preserve them.
        for anchor in (
            "warranty",
            "responsibility",
            "investment",
            "guarantee",
            "fair-use",
            "policy",
        ):
            with self.subTest(anchor=anchor):
                self.assertTrue(
                    self.browser.find_elements(By.ID, anchor),
                    f"#{anchor} disappeared in the conversion",
                )

    def test_faq_renders_each_question_as_its_own_row(self):
        self.browser.get(self.server_url + reverse("faq"))
        rows = self.browser.find_elements(By.CSS_SELECTOR, "article ul > li")
        self.assertGreater(len(rows), 3)
        # The list replaced Materialize's .collection; every child must be an
        # <li>, which the old markup got wrong elsewhere on the site.
        for row in rows:
            self.assertEqual(row.tag_name, "li")

    def test_sitemap_shows_two_columns_and_gates_the_private_one(self):
        self.browser.get(self.server_url + reverse("sitemap"))
        sections = self.browser.find_elements(By.CSS_SELECTOR, "section")
        self.assertEqual(len(sections), 2)
        anonymous = self.browser.page_source
        self.assertNotIn("Change your password", anonymous)

        self.create_cookie_and_go_to_index_page_tier(
            "sitemap@example.com", permission=0
        )
        self.browser.get(self.server_url + reverse("sitemap"))
        self.assertIn("Change your password", self.browser.page_source)

    def test_sitemap_lists_contain_only_list_items(self):
        """Regression: the original nested <div> directly inside <ul>."""
        self.browser.get(self.server_url + reverse("sitemap"))
        for ul in self.browser.find_elements(By.CSS_SELECTOR, "section ul"):
            children = self.browser.execute_script(
                "return Array.from(arguments[0].children).map(c => c.tagName);", ul
            )
            self.assertEqual(set(children), {"LI"})


class SubscriptionsPageTest(FunctionalTest):
    """The pricing table, whose feature rows carry real meaning."""

    def setUp(self):
        super().setUp()
        self.browser.get(self.server_url + reverse("subscriptions"))

    def test_the_four_paid_tiers_render_as_cards(self):
        cards = self.browser.find_elements(By.CSS_SELECTOR, "#user .card")
        self.assertEqual(len(cards), 4)
        self.assertEqual(
            [c.find_element(By.TAG_NAME, "h5").text for c in cards],
            ["Intro", "Asastatser", "Professional", "Cluster"],
        )

    def test_included_and_excluded_features_stay_distinguishable(self):
        """The checkboxes carried information: checked meant "you get this".

        They are no longer inputs, so the distinction has to survive in the
        markup -- otherwise the page silently claims every tier has everything.
        """
        rows = self.browser.find_elements(By.CSS_SELECTOR, "#user ul > li")
        self.assertGreater(len(rows), 30)

        included, excluded = [], []
        for row in rows:
            label = row.find_element(By.TAG_NAME, "span")
            (
                excluded
                if "text-base-content/45" in (label.get_attribute("class") or "")
                else included
            ).append(row)

        self.assertTrue(included, "no feature reads as included")
        self.assertTrue(excluded, "no feature reads as excluded")
        # Every row states itself with exactly one icon, not a toggle.
        for row in rows:
            self.assertEqual(len(row.find_elements(By.TAG_NAME, "svg")), 1)
        self.assertFalse(
            self.browser.find_elements(By.CSS_SELECTOR, "#user input[type='checkbox']"),
            "the feature list still renders inputs the user cannot actually use",
        )

    def test_every_paid_tier_links_out_to_its_subscription(self):
        links = self.browser.find_elements(By.CSS_SELECTOR, "#user .card-actions a")
        self.assertEqual(len(links), 4)
        for link in links:
            self.assertIn("subtopia.io", link.get_attribute("href"))


class IndexSearchTest(FunctionalTest):
    """The address search, on the converted landing page."""

    def test_the_search_field_and_button_survived_the_conversion(self):
        self.browser.get(self.server_url + reverse("index"))
        self.assertTrue(self.find_elem_by_id("id_address").is_displayed())
        button = self.find_elem_by_id("whenmoon")
        # DaisyUI does not upper-case button text the way Materialize did, so
        # the label is asserted case-insensitively: the casing is now a design
        # decision rather than something the content depends on.
        self.assertEqual(button.text.strip().lower(), "when moon")

    def test_a_logged_in_viewer_sees_their_bundles_as_cards(self):
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
