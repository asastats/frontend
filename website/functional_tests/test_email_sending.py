from django.core import mail
from selenium.webdriver.common.by import By

from .base import FunctionalTest


class EmailConfirmationTest(FunctionalTest):
    def test_email_confirmation(self):
        # Wayne signs up
        self.create_cookie_and_go_to_bundlename_add_page("wayne@wayne.com")
        self.accept_cookie()

        # He goes to his emails page
        self.browser.get(self.server_url + "/accounts/email/")

        # He adds his email and confirms
        self.find_elem_by_id("id_email").send_keys("emailconfirm@wayne.com\n")
        self.sleep()
        self.assertIn("Confirmation email sent to ", self.browser.page_source)

        # There's one email sent
        self.assertEqual(len(mail.outbox), 1)

        # and link in it
        first_email = mail.outbox[0]
        for ln in first_email.body.split("\n"):
            if "/accounts/confirm-email/" in ln:
                link = ln.replace("https", "http")
                break

        # He enters that link in his browser
        with self.wait_for_page_load(timeout=5):
            self.browser.get(link)

        # He sees confirmation link and clicks it
        with self.wait_for_page_load(timeout=5):
            self.find_elem_by_id("id_confirm_email").click()

        # He's automatically redirected to his home page afterward
        self.sleep()
        self.assertIn("/home", self.browser.current_url)

    def test_email_verification_resending(self):
        # Dominic signs up
        email = "dominic@wayne.com"
        self.create_cookie_and_go_to_bundlename_add_page(email)
        self.accept_cookie()

        # He goes to his emails page
        self.browser.get(self.server_url + "/accounts/email/")

        # He adds his email and confirms
        self.find_elem_by_id("id_email").send_keys("{}\n".format(email))

        # He sees re-send button and clicks it.
        button = self.browser.find_element(By.NAME, "action_send")
        button.click()
        self.sleep()

        # Now he sees confirmation dialog
        div = self.browser.find_element(By.ID, "id_confirmcontent")
        header = div.find_element(By.TAG_NAME, "h3")
        self.assertIn("Please confirm", header.text)

        # And the text
        paragraph = self.browser.find_element(By.ID, "id_pconfirm")
        self.assertIn("to re-send a verification", paragraph.text)

        # He confirms
        confirm = self.browser.find_element(By.ID, "id_confirm")
        confirm.click()
        self.sleep()

        # There's two emails sent
        self.assertEqual(len(mail.outbox), 2)

        # and link in the second
        second_email = mail.outbox[1]
        for ln in second_email.body.split("\n"):
            if "/accounts/confirm-email/" in ln:
                link = ln.replace("https", "http")
                break

        # He enters that link in his browser
        with self.wait_for_page_load(timeout=5):
            self.browser.get(link)

        # He sees confirmation link with his email
        link = self.browser.find_element(By.LINK_TEXT, email)
        self.assertEqual(link.get_attribute("href"), "mailto:{}".format(email))

    # @pytest.mark.skip(reason="This test fails occasionaly without a proper reason.")
    def test_email_removing(self):
        # Sergei signs up
        email = "sergei@wayne.com"
        self.create_cookie_and_go_to_bundlename_add_page(email)
        self.accept_cookie()

        # He goes to his emails page
        self.browser.get(self.server_url + "/accounts/email/")

        # He adds his email and confirms
        self.find_elem_by_id("id_email").send_keys("{}\n".format(email))

        # He adds another email
        email2 = "sergei2@wayne.com"
        self.find_elem_by_id("id_email").send_keys("{}\n".format(email2))
        self.sleep()
        # He clicks the new email
        radios = [
            elem
            for elem in self.browser.find_elements(By.NAME, "email")
            if elem.get_attribute("id") != "id_email"
        ]
        radios[1].find_element(By.XPATH, "./following-sibling::span").click()
        self.sleep()

        # He sees remove email button and clicks it.
        button = self.browser.find_element(By.NAME, "action_remove")
        button.click()
        self.sleep()

        # Now he sees confirmation dialog
        div = self.browser.find_element(By.ID, "id_confirmcontent")
        header = div.find_element(By.TAG_NAME, "h3")
        self.assertIn("Please confirm", header.text)

        # And the text
        paragraph = self.browser.find_element(By.ID, "id_pconfirm")
        self.assertIn("to remove the selected email", paragraph.text)

        # He confirms
        confirm = self.browser.find_element(By.ID, "id_confirm")
        confirm.click()
        self.sleep()

        # Now he sees only the first email left
        radios = [
            elem
            for elem in self.browser.find_elements(By.NAME, "email")
            if elem.get_attribute("id") != "id_email"
        ]
        self.assertEqual(len(radios), 1)


class EmailResetPasswordTest(FunctionalTest):
    def test_email_reset_password(self):
        # Bruce signs up
        self.create_cookie_and_go_to_bundlename_add_page("bruce@bruce.com")
        self.accept_cookie()

        # He adds an email
        self.browser.get(self.server_url + "/accounts/email/")

        self.find_elem_by_id("id_email").send_keys("bruce1@bruce.com\n")
        self.sleep()
        # He logouts afterward
        with self.wait_for_page_load(timeout=5):
            self.find_elem_by_id("logout").click()

        # He goes to password reset page
        self.browser.get(self.server_url + "/accounts/password/reset/")

        # He adds his email and confirms
        self.find_elem_by_id("id_email").send_keys("bruce1@bruce.com\n")
        self.sleep()
        self.assertIn("We have sent you an email.", self.browser.page_source)

        # There's one email sent
        self.assertEqual(len(mail.outbox), 2)

        # and link in it
        second_email = mail.outbox[1]
        for ln in second_email.body.split("\n"):
            if "/accounts/password/reset/key/" in ln:
                link = ln.replace("https", "http")
                break

        # He enters that link in his browser
        with self.wait_for_page_load(timeout=5):
            self.browser.get(link)

        # He's on page where he can change set new password
        self.assertIn("-set-password/", self.browser.current_url)
