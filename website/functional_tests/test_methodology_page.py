"""Functional tests for the public profit and loss methodology page."""

from django.urls import reverse
from selenium.webdriver.common.by import By

from .base import FunctionalTest

#: Section ids other pages and the PDF may link to.
SECTIONS = (
    "counted",
    "prices",
    "cost-basis",
    "incomplete",
    "own-figures",
    "coverage",
    "gaps",
)


class MethodologyPageTest(FunctionalTest):
    """The page a reader reaches to see how their figures are made."""

    def test_the_footer_leads_to_the_methodology(self):
        self.browser.get(self.server_url + reverse("features"))
        self.find_elem_by_link_text("P&L methodology").click()
        self.wait_for_page_load()
        self.assertTrue(self.browser.current_url.endswith(reverse("methodology")))
        heading = self.browser.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(heading, "How profit and loss is calculated")

    def test_each_section_keeps_its_anchor(self):
        self.browser.get(self.server_url + reverse("methodology"))
        for section in SECTIONS:
            with self.subTest(section=section):
                self.assertTrue(self.browser.find_elements(By.ID, section))

    def test_coverage_and_gaps_are_real_lists(self):
        self.browser.get(self.server_url + reverse("methodology"))
        for section in ("coverage", "gaps"):
            with self.subTest(section=section):
                items = self.browser.find_elements(
                    By.XPATH, f"//h2[@id='{section}']/following-sibling::ul[1]/li"
                )
                self.assertGreater(len(items), 2)

    def test_it_says_it_is_not_tax_advice(self):
        self.browser.get(self.server_url + reverse("methodology"))
        self.assertIn("This is not tax advice.", self.browser.page_source)
