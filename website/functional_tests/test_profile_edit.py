from selenium.webdriver.common.by import By

from .base import FunctionalTest


class ProfileEditTest(FunctionalTest):
    def test_edit_basic_user_data_in_profile_page(self):
        # Robert signs up
        self.create_cookie_and_go_to_bundlename_add_page("dwight@dwight.com")
        self.accept_cookie()

        # On his home page he sees button that links to his profile page
        self.browser.get(self.server_url + "/home/")
        profile = self.find_elem_by_id("id_profile")
        self.assertIn("dwight@dwight.com", profile.text)

        # He clicks the button and goes to edit profile page
        with self.wait_for_page_load(timeout=5):
            profile.click()
        self.assertIn("profile", self.browser.current_url)

        # He sees button that leads to home entitled "Back"
        links = self.browser.find_elements(By.XPATH, '//a[@href="/home/"]')
        self.assertIn("BACK", links[2].text)

        # He sees input box for editing his name
        label_for_name = self.browser.find_element(
            By.XPATH, '//label[@for="id_first_name"]'
        )
        self.assertEqual(label_for_name.text, "First name:")
        # He enters his name
        name = self.find_elem_by_id("id_first_name")
        name.send_keys("Robert")

        # He sees input box for editing his last name
        label_for_lastname = self.browser.find_element(
            By.XPATH, '//label[@for="id_last_name"]'
        )
        self.assertEqual(label_for_lastname.text, "Last name:")

        # He enters his last name and finally submits data
        lastname = self.find_elem_by_id("id_last_name")
        lastname.send_keys("Johnson\n")

        # Just to check he goes to index page and returns to profile afterwards
        with self.wait_for_page_load(timeout=5):
            self.browser.get(self.server_url + "/")
        with self.wait_for_page_load(timeout=5):
            self.browser.get(self.server_url + "/profile/")

        # He sees that his name and lastname are there
        self.assertEqual(
            self.find_elem_by_id("id_first_name").get_attribute("value"), "Robert"
        )
        self.assertEqual(
            self.find_elem_by_id("id_last_name").get_attribute("value"), "Johnson"
        )

    def test_other_user_data_in_profile_page(self):
        # Todd signs up
        self.create_cookie_and_go_to_bundlename_add_page("todd@example.com")
        self.accept_cookie()

        self.browser.get(self.server_url + "/profile/")

        # He sees input box for editing address
        label = self.browser.find_element(
            By.XPATH, '//label[@for="id_profile-0-address"]'
        )
        self.assertEqual(label.text, "Address:")

    def test_profile_page_other_buttons(self):
        # Malcolm signs up
        self.create_cookie_and_go_to_bundlename_add_page("malcolm@malcolm.com")
        self.accept_cookie()

        self.browser.get(self.server_url + "/profile/")

        # He sees there's Emails button leading to accounts emails
        emails = self.find_elem_by_id("id_emails")
        self.assertIn("/accounts/email/", emails.get_attribute("href"))

        # He clicks it and finds himself on email manipulation page
        with self.wait_for_page_load(timeout=5):
            emails.click()
        self.assertIn("email addresses", self.browser.page_source)

        # There's Back button
        back = self.find_elem_by_id("id_back")
        self.assertIn("/profile/", back.get_attribute("href"))

        # He clicks it to get back
        with self.wait_for_page_load(timeout=5):
            back.click()

        # He sees there's social accounts button leading to account connections
        social = self.find_elem_by_id("id_connections")
        self.assertIn("accounts/3rdparty/", social.get_attribute("href"))

        # He clicks it and finds himself on social media manipulation page
        with self.wait_for_page_load(timeout=5):
            social.click()
        self.assertIn("Add a 3rd party account", self.browser.page_source)

        # There's Back button
        back = self.find_elem_by_id("id_back")
        self.assertIn("/profile/", back.get_attribute("href"))

        # He clicks it to get back
        with self.wait_for_page_load(timeout=5):
            back.click()

        # He sees there's social accounts button leading to account connections
        password = self.find_elem_by_id("id_changepassword")
        self.assertIn("/accounts/password/change/", password.get_attribute("href"))

        # He clicks it and finds himself on change password page
        with self.wait_for_page_load(timeout=5):
            password.click()
        self.assertIn("Change password", self.browser.page_source)

        # There's Back button
        back = self.find_elem_by_id("id_back")
        self.assertIn("/profile/", back.get_attribute("href"))

        # He clicks it to get back
        with self.wait_for_page_load(timeout=5):
            back.click()

        # He sees there's API token button
        api = self.find_elem_by_id("id_profile_api")
        self.assertIn("profile/api/", api.get_attribute("href"))

        # He clicks it and finds himself on subscriptions page
        with self.wait_for_page_load(timeout=5):
            api.click()
        self.assertIn("Subscription Model", self.browser.page_source)
