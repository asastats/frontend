"""Functional tests for the subscriptions pricing page.

Its four tier cards each list what the tier includes and what it does not.
That distinction used to be carried by checked and unchecked checkboxes, which
implied a control the reader could operate; it is a two-state feature list now,
and the tests below exist to make sure the "not included" half cannot quietly
disappear.
"""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest


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
