"""Functional tests for the asset feedback form, from a rendered address page."""

from unittest import mock

from django.core.cache import cache
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from assetfeedback.models import AssetFeedback

from .base import FunctionalTest
from .test_address_page import ADDRESS, _sample_payload


class AssetFeedbackFormTest(FunctionalTest):
    """Button to modal to stored report, anonymous and from a cached page."""

    def _open_modal(self):
        self.browser.get(f"{self.server_url}/{ADDRESS}")
        self.browser.find_element(
            By.XPATH, "//summary[contains(., 'not evaluated')]"
        ).click()
        self.browser.find_element(By.CSS_SELECTOR, "[hx-get*='asset-feedback']").click()
        WebDriverWait(self.browser, 10).until(
            lambda browser: browser.find_elements(
                By.CSS_SELECTOR, "#id-asset-feedback-dialog[open]"
            )
        )
        return self.browser.find_element(By.ID, "id-asset-feedback-dialog")

    @mock.patch("assetfeedback.views.MIN_FORM_SECONDS", 0)
    @mock.patch("core.context_processors.fetch_capabilities")
    @mock.patch("core.views.check_export_status")
    @mock.patch("core.views.fetch_and_serialize_account")
    def test_anonymous_reader_sends_a_report(self, mocked_fetch, mocked_status, mocked_caps):
        cache.clear()
        mocked_fetch.return_value = _sample_payload()
        mocked_status.return_value = {}
        mocked_caps.return_value = {"permission": 0}

        dialog = self._open_modal()
        dialog.find_element(By.NAME, "details").send_keys("Sold on a gallery")
        dialog.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

        wait = WebDriverWait(self.browser, 10)
        wait.until(
            lambda browser: "Thank you"
            in browser.find_element(By.CSS_SELECTOR, "#id-asset-feedback-dialog[open]").text
        )
        report = AssetFeedback.objects.get()
        self.assertEqual(report.details, "Sold on a gallery")
        self.assertIsNone(report.user)

        self.browser.find_element(By.CSS_SELECTOR, "[data-asset-feedback-close]").click()
        wait.until(
            lambda browser: not browser.find_elements(
                By.CSS_SELECTOR, "#id-asset-feedback-dialog[open]"
            )
        )
