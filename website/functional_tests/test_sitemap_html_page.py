from .base import FunctionalTest


class SitemapHtmlPageTest(FunctionalTest):
    def test_sitemap_html_page(self):
        # Urlike checks sitemap page
        self.browser.get(self.server_url + "/sitemap/")

        # She notices there's Public and Private pages headers
        headers = self.find_elems_by_tag("h3")
        self.assertIn("Public pages", [header.text for header in headers])
        self.assertIn("Private pages", [header.text for header in headers])

        # Now she logs in
        self.create_cookie_and_go_to_bundlename_add_page("urlike@urlike.com")
        self.accept_cookie()

        # And visits sitemap page again
        self.browser.get(self.server_url + "/sitemap/")

        # She notices various user related links
        home = self.find_elem_by_link_text("Home page")
        self.assertIn("/home/", home.get_attribute("href"))
        social = self.find_elem_by_link_text("Your social accounts")
        self.assertIn("/accounts/3rdparty/", social.get_attribute("href"))
        signup = self.find_elem_by_link_text("User signup")
        self.assertIn("/accounts/signup/", signup.get_attribute("href"))
        login = self.find_elem_by_link_text("User login")
        self.assertIn("/accounts/login/", login.get_attribute("href"))
        change_password = self.find_elem_by_link_text("Change your password")
        self.assertIn(
            "/accounts/password/change/", change_password.get_attribute("href")
        )
        reset_password = self.find_elem_by_link_text("Reset your password")
        self.assertIn("/accounts/password/reset/", reset_password.get_attribute("href"))

        # She clicks on reset password link
        reset_password.click()

        # She finds herself on reset password page
        header = self.find_elem_by_tag("h2")
        self.assertIn("Forgotten your password?", header.text)
