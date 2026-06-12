"""Testing module for website's synchronous url dispatcher module."""

from django.urls import URLPattern, URLResolver

from asastats import urls
from asastats.sitemaps import PrioritizedStaticViewSitemap, StaticViewSitemap


class TestAsastatsUrls:
    """Testing class for :py:mod:`asastats.asastats.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    def test_asastats_urls_sitemap_xml(self):
        url = self._url_from_pattern("sitemap.xml")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "django.contrib.sitemaps.views.sitemap"
        assert url.name == "django.contrib.sitemaps.views.sitemap"
        assert url.default_args == {
            "sitemaps": {
                "statichp": PrioritizedStaticViewSitemap,
                "static": StaticViewSitemap,
            }
        }

    def test_asastats_urls_sitemap(self):
        url = self._url_from_pattern(r"^sitemap/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "django.contrib.sitemaps.views.sitemap"
        assert url.name == "sitemap"
        assert url.default_args == {
            "sitemaps": {
                "statichp": PrioritizedStaticViewSitemap,
                "static": StaticViewSitemap,
            },
            "template_name": "sitemap.html",
            "content_type": None,
        }

    def test_asastats_urls_api_app(self):
        url = self._url_from_pattern(r"^api/v2/")
        assert isinstance(url, URLResolver)
        assert "api.urls" in str(url.urlconf_name)

    def test_asastats_urls_widgets_app(self):
        url = self._url_from_pattern(r"^widgets/")
        assert isinstance(url, URLResolver)
        assert "widgets.urls" in str(url.urlconf_name)

    def test_asastats_urls_core_app(self):
        url = self._url_from_pattern(r"^")
        assert isinstance(url, URLResolver)
        assert "core.urls" in str(url.urlconf_name)

    def test_asastats_urls_patterns_count(self):
        assert len(urls.urlpatterns) == 8

    def test_asastats_urls_defines_custom_handler500(self):
        assert getattr(urls, "handler500") == "core.views.custom_server_error"
