from selenium.webdriver.common.by import By

from .base import FunctionalTest


class SitemapHtmlPageTest(FunctionalTest):
    def test_sitemap_html_page(self):
        # Urlike checks sitemap page
        self.browser.get(self.server_url + "/sitemap/")

        # She notices there's Public and Private pages headers. The level is a
        # design decision -- they became <h2> under the page's <h1> in the
        # redesign -- so the assertion is that the headings exist, not what
        # they are made of.
        headings = [
            h.text
            for h in self.browser.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
        ]
        self.assertIn("Public pages", headings)
        self.assertIn("Private pages", headings)

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


class SitemapStructureTest(FunctionalTest):
    """The page's two columns, and what each shows to whom."""

    def test_sitemap_shows_two_columns_and_gates_the_private_one(self):
        self.browser.get(self.server_url + "/sitemap/")
        sections = self.browser.find_elements(By.CSS_SELECTOR, "section")
        self.assertEqual(len(sections), 2)
        self.assertNotIn("Change your password", self.browser.page_source)

        self.create_cookie_and_go_to_index_page_tier(
            "sitemap@example.com", permission=0
        )
        self.browser.get(self.server_url + "/sitemap/")
        self.assertIn("Change your password", self.browser.page_source)

    def test_sitemap_lists_contain_only_list_items(self):
        """Regression: the markup nested a <div> directly inside a <ul>."""
        self.browser.get(self.server_url + "/sitemap/")
        for ul in self.browser.find_elements(By.CSS_SELECTOR, "section ul"):
            children = self.browser.execute_script(
                "return Array.from(arguments[0].children).map(c => c.tagName);", ul
            )
            self.assertEqual(set(children), {"LI"})
