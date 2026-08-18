"""The sitemap must publish the site's own domain, not a hardcoded one.

`django.contrib.sites` ships one row whose domain is `example.com`, and the
sitemap views build every absolute URL from it. Nothing warns when that row is
never updated: the page renders, the XML validates, and every URL in it points
at a domain nobody owns -- `/sitemap/` showing it to readers and `/sitemap.xml`
to search engines.

Setting the row is provisioning's job, not the code's, so what is pinned here
is the wiring: whatever the row says is what the sitemap publishes. The row is
set inside each test rather than assumed, so these pass on any deployment and
would fail if a domain were ever written into a template or a setting.
"""

from urllib.parse import urlparse

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse

#: Deliberately not the real domain: a test that used it could pass on a
#: template that hardcoded the real one.
TEST_DOMAIN = "sitemap-test.example.org"


class SitemapUrlTest(TestCase):
    """Testing class for the domain the sitemap publishes."""

    def setUp(self):
        Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={"domain": TEST_DOMAIN, "name": "Sitemap Test"},
        )
        # `get_current()` memoises per SITE_ID for the process, so a row
        # changed mid-test is invisible without this.
        Site.objects.clear_cache()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_core_sitemap_page_publishes_the_configured_domain(self):
        response = self.client.get(reverse("sitemap"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn(TEST_DOMAIN, html)

    def test_core_sitemap_page_hardcodes_no_domain(self):
        """Django's placeholder is the one that actually shipped."""
        response = self.client.get(reverse("sitemap"))

        self.assertNotIn("example.com", response.content.decode())

    def test_core_sitemap_xml_publishes_the_configured_domain(self):
        """The one crawlers read, and the reason this matters beyond looks."""
        response = self.client.get("/sitemap.xml")
        xml = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn(TEST_DOMAIN, xml)
        self.assertNotIn("example.com", xml)

    def test_core_sitemap_xml_uses_the_configured_protocol(self):
        """Whatever this environment sets, not a scheme derived from elsewhere.

        `SITEMAP_PROTOCOL` is layered per environment: http in base, because a
        locally served site is http, raised to https in production.py. Deriving
        it from WEBSITE_URL instead would force https on the dev server, which
        is why this asserts the setting is used rather than what it should be.
        """
        response = self.client.get("/sitemap.xml")

        self.assertIn(
            f"{settings.SITEMAP_PROTOCOL}://{TEST_DOMAIN}", response.content.decode()
        )


class WebsiteDomainSettingTest(TestCase):
    """`WEBSITE_DOMAIN` is a host, and templates use it as one."""

    def test_core_website_domain_is_a_host_not_a_url(self):
        """It was read straight from the WEBSITE_URL env var.

        The mobile privacy page renders `info@{{ WEBSITE_DOMAIN }}`, which came
        out as `info@https://www.asastats.com`.
        """
        self.assertNotIn("://", settings.WEBSITE_DOMAIN)
        self.assertNotIn("/", settings.WEBSITE_DOMAIN)

    def test_core_website_domain_matches_the_website_url(self):
        self.assertEqual(
            settings.WEBSITE_DOMAIN, urlparse(settings.WEBSITE_URL).netloc
        )

    def test_core_website_domain_renders_as_an_address(self):
        """The page it appears on has to read as an email address."""
        response = self.client.get(reverse("asm_privacy"))
        html = response.content.decode()

        self.assertIn(f"info@{settings.WEBSITE_DOMAIN}", html)
        self.assertNotIn("info@https", html)
