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

    def test_account_deletion_page_is_public_and_says_when(self):
        # Play Console links this page, so it must open without signing in.
        self.browser.get(self.server_url + reverse("account_deletion"))

        self.assertEqual(
            self.browser.find_element(By.TAG_NAME, "h1").text, "Delete your account"
        )
        body = self.browser.find_element(By.TAG_NAME, "body").text
        self.assertIn("permanently deleted within 7 days", body)
        for anchor in ("how", "when", "what", "kept", "contact"):
            with self.subTest(anchor=anchor):
                self.assertTrue(self.browser.find_elements(By.ID, anchor))

    def test_app_privacy_policy_covers_what_the_stores_ask(self):
        # The store listings point at this URL; App Review and Play's Data
        # safety review read it against what the app collects.
        self.browser.get(self.server_url + reverse("asm_privacy"))

        for anchor in (
            "collected",
            "third-parties",
            "retention",
            "deletion",
            "children",
            "contact",
        ):
            with self.subTest(anchor=anchor):
                self.assertTrue(self.browser.find_elements(By.ID, anchor))
        link = self.browser.find_element(By.CSS_SELECTOR, "#deletion + div a")
        self.assertTrue(link.get_attribute("href").endswith(reverse("account_deletion")))
