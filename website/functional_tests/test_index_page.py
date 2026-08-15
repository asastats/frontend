from django.contrib.auth import get_user_model
from django.urls import reverse
from selenium.webdriver.common.by import By

from core.models import BundleName

from .base import TESTING_ADDRESS, FunctionalTest


class IndexPageTest(FunctionalTest):
    def test_index_page_has_whenmoon_button_that_leads_to_address_page(self):
        self.browser.get(self.server_url)

        self.assertIn("ASA Stats", self.browser.title)

        address = self.find_elem_by_id("id_address")
        address.clear()
        address.send_keys(TESTING_ADDRESS)

        button = self.find_elem_by_id("whenmoon")
        # Materialize upper-cased button text in CSS; DaisyUI does not, so the
        # rendered casing is now a design choice rather than content.
        self.assertEqual(button.text.strip().lower(), "when moon")

        with self.wait_for_page_load(timeout=2):
            self.find_elem_by_id("whenmoon").click()
        self.assertIn(TESTING_ADDRESS, self.browser.current_url)


class IndexPageContentTest(FunctionalTest):
    """What the landing page shows before anyone searches."""

    def test_the_search_field_and_button_are_present(self):
        self.browser.get(self.server_url + reverse("index"))
        self.assertTrue(self.find_elem_by_id("id_address").is_displayed())
        button = self.find_elem_by_id("whenmoon")
        self.assertEqual(button.text.strip().lower(), "when moon")

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
