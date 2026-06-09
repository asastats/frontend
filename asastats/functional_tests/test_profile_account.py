from selenium.webdriver.common.by import By

from .base import FunctionalTest


class ProfileAccountTest(FunctionalTest):
    def test_profile_account_page_components(self):
        # Gary signs up
        self.create_cookie_and_go_to_bundlename_add_page("gary15@dwight.com")
        self.accept_cookie()

        # On his home page he sees button that links to his profile page
        self.browser.get(self.server_url + "/home/")
        profile = self.find_elem_by_id("id_profile")
        # He clicks the button and goes to edit profile page
        with self.wait_for_page_load(timeout=5):
            profile.click()
        self.assertIn("profile", self.browser.current_url)

        # He sees button that leads to account entitled "Account"
        link = self.browser.find_element(By.XPATH, '//a[@href="/profile/account/"]')
        self.assertIn("ACCOUNT", link.text)

        # He clicks it
        with self.wait_for_page_load(timeout=5):
            link.click()

        # He notices there's header with his email
        header = self.find_elem_by_tag("h2")
        self.assertIn("gary15@dwight.com profile account", header.text)

        # He sees button that leads to profile page entitled "Back"
        links = self.browser.find_elements(By.XPATH, '//a[@href="/profile/"]')
        self.assertIn("BACK", links[0].text)

        # He sees there's deactivate account button leading to deactivate page
        deactivate = self.find_elem_by_id("id_deactivate")
        self.assertIn("/profile/deactivate/", deactivate.get_attribute("href"))

        # He clicks it and finds himself on deactivate account page
        with self.wait_for_page_load(timeout=5):
            deactivate.click()
        self.assertIn("Deactivate account", self.browser.page_source)

        # He sees the captcha image
        form = self.find_elem_by_id("deactivate_profile")
        captcha_image = form.find_element(By.TAG_NAME, "img")
        self.assertIn("/captcha/image/", captcha_image.get_attribute("src"))

        # He sees the captcha input box too
        captcha_input = self.find_elem_by_id("id_captcha_1")
        self.assertEqual("captcha_1", captcha_input.get_attribute("name"))
