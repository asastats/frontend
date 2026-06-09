from selenium.webdriver.common.by import By

from .base import BROWSER_DRIVER, FunctionalTest


class CustomAuthTest(FunctionalTest):
    def test_custom_auth_page(self):
        # Don goes to signup page
        with self.wait_for_page_load(timeout=5):
            self.browser.get(self.server_url + "/accounts/signup/")

        self.accept_cookie()

        # He sees sign up header
        header = self.find_elem_by_tag("h3")
        self.assertIn("Sign up", header.text)

        # He sees input field for login with hint text in it
        elem = self.find_elem_by_id("id_email")
        self.assertIn("Email address", elem.get_attribute("placeholder"))

        # Also input field for password with hint text in it
        elem = self.browser.find_element(By.XPATH, '//label[@for="id_password1"]')
        self.assertIn("Password", elem.text)

        # And another input field for password
        elem = self.browser.find_element(By.XPATH, '//label[@for="id_password2"]')
        self.assertIn("Password (again)", elem.text)

        # There are login by social media account buttons too
        social = self.find_elem_by_id("id_discord")
        self.assertIn("/accounts/discord/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_twitter")
        self.assertIn("/accounts/twitter_oauth2/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_reddit")
        self.assertIn("/accounts/reddit/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_github")
        self.assertIn("/accounts/github/login/", social.get_attribute("href"))
        social = self.find_elem_by_id("id_google")
        self.assertIn("/accounts/google/login/", social.get_attribute("href"))

        buttons = self.browser.find_elements(By.CLASS_NAME, "primaryAction")
        self.assertIn("Sign up".upper(), buttons[0].text)

        # There's the button asking if he maybe already has an account
        links = self.browser.find_elements(By.XPATH, '//a[@href="/accounts/login/"]')
        self.assertIn("Already have an account?".upper(), links[1].text)

        # He clicks that button and finds himself in login page
        with self.wait_for_page_load(timeout=5):
            links[1].click()

        # He sees sign up header
        header = self.find_elem_by_tag("h3")
        self.assertIn("Login", header.text)

        # He sees input field for login with hint text in it
        elem = self.find_elem_by_id("id_login")
        self.assertIn("Username or email", elem.get_attribute("placeholder"))

        # Also input field for password with hint text in it
        elem = self.browser.find_element(By.XPATH, '//label[@for="id_password"]')
        self.assertIn("Password", elem.text)

        # There are login by social media account buttons too
        text = "Sign in with Discord"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/discord/login/", social.get_attribute("href"))
        text = "Sign in with X"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/twitter_oauth2/login/", social.get_attribute("href"))
        text = "Sign in with Reddit"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/reddit/login/", social.get_attribute("href"))
        text = "Sign in with GitHub"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/github/login/", social.get_attribute("href"))
        text = "Sign in with Google"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/google/login/", social.get_attribute("href"))

        # There's the button asking if he maybe don't have an account
        links = self.browser.find_elements(By.XPATH, '//a[@href="/accounts/signup/"]')
        self.assertIn("Don't have an account?".upper(), links[1].text)

        # Also the button asking if he maybe forgot his password
        links = self.browser.find_elements(
            By.XPATH, '//a[@href="/accounts/password/reset/"]'
        )
        self.assertIn("Forgot your password?", links[0].text)

        # # There's help button
        # elem = self.find_elem_by_id('id_help_auth')
        # self.assertIn("Help".upper(), elem.text)

        # There's large call to action button
        buttons = self.browser.find_elements(By.CLASS_NAME, "primaryAction")
        self.assertIn("Log in".upper(), buttons[0].text)

    def test_modal_custom_auth_page(self):
        # Dan goes to index page
        with self.wait_for_page_load(timeout=5):
            self.browser.get(self.server_url)

        self.accept_cookie()

        # He sees login link and clicks it
        login = self.browser.find_element(By.XPATH, '//a[@href="#modalLogin"]')
        login.click()
        self.sleep()
        # He sees sign up header
        container = self.find_elem_by_class("modal-content")
        header = container.find_element(By.TAG_NAME, "h3")
        self.assertIn("Log in", header.text)

        # He sees input field for login with hint text in it
        elem = self.find_elem_by_id("id_login_modal")
        self.assertIn("Username or email", elem.get_attribute("placeholder"))

        # Also input field for password with hint text in it
        elem = self.find_elem_by_id("id_password_modal")
        self.assertIn("Password", elem.get_attribute("placeholder"))

        # # TODO uncomment this if we solve checkbox bug
        # # And password remember field
        # elem = self.find_elem_by_id('id_remember_modal')
        # self.assertEqual('checkbox', elem.get_attribute('type'))

        # There are login by social media account buttons too
        # There are login by social media account buttons too
        text = "Sign in with Discord"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/discord/login/", social.get_attribute("href"))
        text = "Sign in with X"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/twitter_oauth2/login/", social.get_attribute("href"))
        text = "Sign in with Reddit"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/reddit/login/", social.get_attribute("href"))
        text = "Sign in with GitHub"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/github/login/", social.get_attribute("href"))
        text = "Sign in with Google"
        social = self.browser.find_element(
            By.LINK_TEXT, text if BROWSER_DRIVER == "Firefox" else text.upper()
        )
        self.assertIn("/accounts/google/login/", social.get_attribute("href"))
        # There's the button asking if he maybe don't have an account
        links = self.browser.find_elements(By.XPATH, '//a[@href="/accounts/signup/"]')
        self.assertIn("Don't have an account?".upper(), links[0].text)

        # Also the button asking if he maybe forgot his password
        links = self.browser.find_elements(
            By.XPATH, '//a[@href="/accounts/password/reset/"]'
        )
        self.assertIn("Forgot Password?".upper(), links[0].text)

        # There's cancel button
        elem = self.find_elem_by_id("id_cancel")
        self.assertIn("Cancel".upper(), elem.text)

        # And there's call to action button
        elem = self.find_elem_by_id("id_cta_modal")
        self.assertIn("Log in".upper(), elem.text)
