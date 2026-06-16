# -*- coding: utf-8 -*-
from unittest import skip

from django.urls import reverse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base import FunctionalTest

# from selenium.webdriver.support.ui import WebDriverWait


# from django.utils.translation import activate


class SocialLogin(FunctionalTest):

    # NOTE test passed and skipped in early development phase
    # Should uncomment following too
    # fixtures = ['initial_fixture']

    def setUp(self):
        # activate('en')
        super().setUp()
        # self.browser.wait = WebDriverWait(self.browser, 3)

    def get_element_by_id(self, element_id):
        WebDriverWait(self.browser, 5).until(
            EC.presence_of_element_located((By.ID, element_id))
        )

    def get_button_by_id(self, element_id):
        WebDriverWait(self.browser, 5).until(
            EC.element_to_be_clickable((By.ID, element_id))
        )

    def get_full_url(self, namespace):
        return self.server_url + reverse(namespace)

    def get_credentials(self):
        import json
        import os

        from django.conf import settings

        with open(
            os.path.join(settings.FIXTURE_DIRS[0], "{}_user.json".format(self.provider))
        ) as f:
            return json.loads(f.read())

    def social_login(self):
        self.browser.get(self.get_full_url("index"))
        social_login = self.get_element_by_id("{}_login".format(self.provider))
        with self.assertRaises(TimeoutException):
            self.get_element_by_id("logout")
        self.assertEqual(
            social_login.get_attribute("href"),
            self.live_server_url + "/accounts/{}/login".format(self.provider),
        )
        social_login.click()
        self.user_login()
        with self.assertRaises(TimeoutException):
            self.get_element_by_id("{}_login".format(self.provider))
        social_logout = self.get_element_by_id("logout")
        social_logout.click()
        social_login = self.get_element_by_id("{}_login".format(self.provider))


class TestGoogleLogin(SocialLogin):

    provider = "google"

    def user_login(self):
        credentials = self.get_credentials()
        self.get_element_by_id("Email").send_keys(credentials["Email"])
        self.get_button_by_id("next").click()
        self.get_element_by_id("Passwd").send_keys(credentials["Passwd"])
        for btn in ["signIn", "submit_approve_access"]:
            self.get_button_by_id(btn).click()
        return None

    @skip  # NOTE test passed and skipped in early development phase
    def test_google_login(self):
        super().social_login()


class TestTwitterLogin(SocialLogin):

    provider = "twitter"

    def user_login(self):
        credentials = self.get_credentials()
        for key, value in credentials.items():
            self.get_element_by_id(key).send_keys(value)
        for btn in ["allow"]:
            self.get_button_by_id(btn).click()
        return None

    @skip  # NOTE test passed and skipped in early development phase
    def test_twitter_login(self):
        super().social_login()
