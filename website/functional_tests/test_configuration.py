
from utils.helpers import load_transparency_reports

from .base import FunctionalTest

SITEMAP_URLS = (
    "about",
    "tokenomics",
    "faq",
    "features",
    "subscriptions",
    "disclaimer",
    "asm-privacy",
    "accounts/signup",
    "accounts/login",
    "accounts/password/reset",
)
SITEMAP_FILES = ("whitepaper.pdf",)


class ConfigurationTest(FunctionalTest):
    def test_robots_file(self):
        self.browser.get(self.server_url + "/robots.txt")
        self.assertIn("User-agent", self.browser.page_source)

    def test_auth_privacy_file(self):
        self.browser.get(self.server_url + "/static/auth_privacy.html")
        self.assertIn("<h1>Privacy policy</h1>", self.browser.page_source)

    def test_auth_terms_file(self):
        self.browser.get(self.server_url + "/static/auth_terms.html")
        self.assertIn("<h1>Terms of use</h1>", self.browser.page_source)

    def test_sitemap_urls(self):
        self.browser.get(self.server_url + "/sitemap.xml")
        for url in SITEMAP_URLS:
            self.assertIn("/{}/".format(url), self.browser.page_source)

    def test_transparency_report_files(self):
        self.browser.get(self.server_url + "/sitemap.xml")
        
        for year_group in load_transparency_reports():
            for report in year_group["months"]:
                expected_url = f"/transparency-report-{report['year']}-{report['month']}.pdf"
                self.assertIn(
                    expected_url,
                    self.browser.page_source,
                )
                print(expected_url)

    def test_sitemap_files(self):
        self.browser.get(self.server_url + "/sitemap.xml")

        for url in SITEMAP_FILES:
            self.assertIn("/{}".format(url), self.browser.page_source)
