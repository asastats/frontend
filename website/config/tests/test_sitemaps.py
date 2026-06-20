"""Testing module for website's sitemap pages."""

from datetime import datetime
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from config.sitemaps import (
    PUBLISHING_DATE,
    PrioritizedStaticViewSitemap,
    StaticViewSitemap,
)
from utils.helpers import load_transparency_reports


class SitemapTest(TestCase):
    def setUp(self):
        self.sitemap = StaticViewSitemap()
        self.items = self.sitemap.items()

    def check_for_sole_item(self, item):
        self.assertIn(item, [value for value, _ in self.items])

    def check_for_item_with_args(self, item):
        self.assertIn(item, [value for value in self.items])

    def test_sitemap_changefreq_set_to_weekly(self):
        self.assertEqual(self.sitemap.changefreq, "daily")

    def test_sitemap_protocol_is_set_as_settings_const(self):
        self.assertEqual(self.sitemap.protocol, settings.SITEMAP_PROTOCOL)

    def test_sitemap_protocol_prioritized_is_set_as_settings_const(self):
        self.assertEqual(
            PrioritizedStaticViewSitemap().protocol, settings.SITEMAP_PROTOCOL
        )

    def test_sitemap_priority_set_to_half(self):
        self.assertEqual(self.sitemap.priority, 0.5)

    def test_sitemap_covers_about_page(self):
        self.check_for_sole_item("about")

    def test_sitemap_covers_tokenomics_page(self):
        self.check_for_sole_item("tokenomics")

    def test_sitemap_covers_faq_page(self):
        self.check_for_sole_item("faq")

    def test_sitemap_covers_disclaimer_page(self):
        self.check_for_sole_item("disclaimer")

    def test_sitemap_covers_features_page(self):
        self.check_for_sole_item("features")

    def test_sitemap_covers_subscriptions_page(self):
        self.check_for_sole_item("subscriptions")

    def test_sitemap_covers_asa_stats_mobile_privacy_page(self):
        self.check_for_sole_item("asm_privacy")

    def test_sitemap_covers_privacy_page(self):
        self.check_for_item_with_args(("html_file", ["auth_privacy.html"]))

    def test_sitemap_covers_terms_page(self):
        self.check_for_item_with_args(("html_file", ["auth_terms.html"]))

    def test_sitemap_covers_account_signup_page(self):
        self.check_for_sole_item("account_signup")

    def test_sitemap_covers_account_login_page(self):
        self.check_for_sole_item("account_login")

    def test_sitemap_covers_account_reset_password_page(self):
        self.check_for_sole_item("account_reset_password")

    def test_sitemap_covers_whitepaper_pdf(self):
        self.check_for_item_with_args(("assets_file", ["whitepaper.pdf"]))

    def test_sitemap_covers_transparecy_report_pdfs(self):
        reports = [
            {
                "year": 2026,
                "months": [
                    {
                        "year": "2026",
                        "month": "05",
                        "short_year": "26",
                        "month_name": "May",
                    },
                    {
                        "year": "2026",
                        "month": "04",
                        "short_year": "26",
                        "month_name": "April",
                    },
                    {
                        "year": "2026",
                        "month": "03",
                        "short_year": "26",
                        "month_name": "March",
                    },
                    {
                        "year": "2026",
                        "month": "02",
                        "short_year": "26",
                        "month_name": "February",
                    },
                    {
                        "year": "2026",
                        "month": "01",
                        "short_year": "26",
                        "month_name": "January",
                    },
                ],
            },
            {
                "year": 2025,
                "months": [
                    {
                        "year": "2025",
                        "month": "12",
                        "short_year": "25",
                        "month_name": "December",
                    },
                    {
                        "year": "2025",
                        "month": "11",
                        "short_year": "25",
                        "month_name": "November",
                    },
                    {
                        "year": "2025",
                        "month": "10",
                        "short_year": "25",
                        "month_name": "October",
                    },
                ],
            },
        ]
        mock.patch("config.sitemaps.load_transparency_reports", return_value=reports)
        for year_group in load_transparency_reports():
            for report in year_group["months"]:
                self.check_for_item_with_args(
                    (
                        "assets_file",
                        [f"transparency-report-{report['year']}-{report['month']}.pdf"],
                    )
                )

    def test_location_returns_url_for_supplied_sole_item(self):
        location = self.sitemap.location(("about", ()))
        self.assertEqual(location, reverse("about"))

    def test_prioritized_sitemap_has_highest_priority(self):
        sitemap = PrioritizedStaticViewSitemap()
        self.assertEqual(sitemap.priority, 1.0)

    def test_sitemap_covers_index_page(self):
        sitemap = PrioritizedStaticViewSitemap()
        self.assertIn("index", [value for value, _ in sitemap.items()])

    def test_sitemap_page_renders_sitemap_template(self):
        response = self.client.get("/sitemap/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sitemap.html")

    def test_sitemap_contains_static_page_item(self):
        response = self.client.get(reverse("sitemap"))
        self.assertContains(response, "/disclaimer/")

    def test_sitemap_lastmod_returns_publishing_date(self):
        self.assertEqual(self.sitemap.lastmod(("bla", ())), PUBLISHING_DATE)

    def test_sitemap_lastmod_returns_provided_date(self):
        date = datetime(2018, 1, 1)
        self.assertEqual(self.sitemap.lastmod(("bla", (), date)), date)

    def test_sitemap_lastmod_returns_const_for_wrong_type(self):
        date = "bla"
        self.assertEqual(self.sitemap.lastmod(("bla", (), date)), PUBLISHING_DATE)

    def test_sitemap_lastmod_prioritized_returns_publishing_date(self):
        sitemap = PrioritizedStaticViewSitemap()
        self.assertEqual(sitemap.lastmod(("bla", ())), PUBLISHING_DATE)

    def test_sitemap_lastmod_prioritized_returns_provided_date(self):
        sitemap = PrioritizedStaticViewSitemap()
        date = datetime(2018, 1, 1)
        self.assertEqual(sitemap.lastmod(("bla", (), date)), date)

    def test_sitemap_lastmod_prioritized_returns_const_for_wrong_type(self):
        sitemap = PrioritizedStaticViewSitemap()
        date = 8
        self.assertEqual(sitemap.lastmod(("bla", (), date)), PUBLISHING_DATE)
