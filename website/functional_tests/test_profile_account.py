from selenium.webdriver.common.by import By

from .base import FunctionalTest


class ProfileAccountTest(FunctionalTest):
    def test_profile_account_page_components(self):
        # Gary signs up
        self.create_cookie_and_go_to_bundlename_add_page("gary15@dwight.com")

        # On his home page he sees button that links to his profile page
        self.browser.get(self.server_url + "/home/")
        profile = self.find_elem_by_id("id_profile")
        # He clicks the button and goes to edit profile page
        with self.wait_for_page_load(timeout=5):
            profile.click()
        self.assertIn("profile", self.browser.current_url)

        # He sees button that leads to account entitled "Account"
        link = self.browser.find_element(By.XPATH, '//a[@href="/profile/account/"]')
        # Materialize upper-cased button and link text in CSS; DaisyUI does
        # not, so the rendered casing is a design decision now rather than
        # something the content depends on.
        self.assertIn("account", link.text.lower())

        # He clicks it
        with self.wait_for_page_load(timeout=5):
            link.click()

        # He notices there's header with his email
        #
        # An h1, not an h2: base_profile makes the page title the document's
        # top-level heading, where base_home had it one level down. Looking for
        # an h2 now finds the first footer group heading instead.
        header = self.find_elem_by_tag("h1")
        self.assertIn("gary15@dwight.com profile account", header.text)

        # He sees button that leads to profile page entitled "Back"
        #
        # Matched by text, not position: the breadcrumb and the section sub-nav
        # both link to /profile/ now, so an index here tracks the chrome rather
        # than the button.
        links = self.browser.find_elements(By.XPATH, '//a[@href="/profile/"]')
        self.assertTrue(
            any(link.text.strip().lower() == "back" for link in links),
            "the account page has no Back button leading to the profile",
        )

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


class ProfileAccountHierarchyTest(FunctionalTest):
    """The one destructive action on the page has to look like one.

    The page was rebuilt from a 7/5 column split that put the subscription tier
    and the deactivate link side by side, as though a status and the most
    destructive action in the account were two comparable things. They are two
    sections now, deactivation last, and the control is marked.

    Measured rather than read off the class list: `btn-error` is only a promise
    until the stylesheet is built, and Tailwind scans templates -- a class
    written after the last build is not compiled and paints nothing. That has
    happened on this project.
    """

    def setUp(self):
        super().setUp()
        self.create_cookie_and_go_to_index_page_tier("hierarchy@dwight.com", permission=100)
        self.browser.get(self.server_url + "/profile/account/")

    def _computed(self, element, prop):
        return self.browser.execute_script(
            "return getComputedStyle(arguments[0])[arguments[1]];", element, prop
        )

    def test_the_deactivate_control_is_painted_as_destructive(self):
        deactivate = self.find_elem_by_id("id_deactivate")
        back = next(
            link
            for link in self.browser.find_elements(By.CSS_SELECTOR, "main a.btn")
            if link.text.strip().lower() == "back"
        )

        error_colour = self._computed(deactivate, "color")
        self.assertNotEqual(
            error_colour,
            self._computed(back, "color"),
            "the deactivate control is painted exactly like the Back button",
        )
        # Against the theme's own error token, so this follows the theme
        # instead of pinning one palette.
        expected = self.browser.execute_script(
            "var probe = document.createElement('span');"
            "probe.className = 'text-error';"
            "document.body.appendChild(probe);"
            "var colour = getComputedStyle(probe).color;"
            "probe.remove();"
            "return colour;"
        )
        self.assertEqual(expected, error_colour)

    def test_the_destructive_action_comes_last(self):
        """Below the status it used to sit beside.

        Source order, which is also the order a phone stacks them in.
        """
        deactivate = self.find_elem_by_id("id_deactivate")
        tier_section = self.browser.find_elements(By.CSS_SELECTOR, "main section")[0]

        self.assertGreater(
            deactivate.location["y"],
            tier_section.location["y"] + tier_section.size["height"] - 1,
        )

    def test_it_still_reaches_the_confirmation_page(self):
        """Marked as destructive, and not disarmed.

        The deactivate page asks for a captcha; the control's job is to get
        there.
        """
        with self.wait_for_page_load(timeout=5):
            self.find_elem_by_id("id_deactivate").click()

        self.assertIn("/profile/deactivate/", self.browser.current_url)
        self.assertTrue(self.browser.find_elements(By.ID, "deactivate_profile"))
