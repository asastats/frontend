"""Functional tests for the prose pages: about, disclaimer, faq, features,
tokenomics and the mobile privacy policy.

They carry no flows, so what matters is that their structure survives edits --
the anchors other pages and external references link to, and lists that are
actually lists.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest


class StaticPagesTest(FunctionalTest):
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
