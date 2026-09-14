"""Testing module for website's synchronous url dispatcher module."""

from django.urls import URLPattern, URLResolver

from config import urls
from config.sitemaps import PrioritizedStaticViewSitemap, StaticViewSitemap


class TestAsastatsUrls:
    """Testing class for :py:mod:`website.config.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    def test_config_urls_sitemap_xml(self):
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

    def test_config_urls_sitemap(self):
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

    def test_config_urls_api_app(self):
        url = self._url_from_pattern(r"^api/v2/")
        assert isinstance(url, URLResolver)
        assert "api.urls" in str(url.urlconf_name)

    def test_config_urls_widgets_app(self):
        url = self._url_from_pattern(r"^widgets/")
        assert isinstance(url, URLResolver)
        assert "widgets.urls" in str(url.urlconf_name)

    def test_config_urls_core_app(self):
        url = self._url_from_pattern(r"^")
        assert isinstance(url, URLResolver)
        assert "core.urls" in str(url.urlconf_name)

    def test_config_urls_patterns_count(self):
        """Nine since the root assets joined: the count is a guard, not a fact.

        It exists so a route added without thought about *order* is noticed,
        this urlconf ending in a catch-all that swallows anything a pattern
        above it did not claim. `ROOT_ASSETS` is exactly that case - the
        favicons and the manifest had been resolving as bundle names - so the
        number moves with a reason recorded, rather than being edited to make a
        red test green.
        """
        assert len(urls.urlpatterns) == 9

    def test_config_urls_defines_custom_handler500(self):
        assert getattr(urls, "handler500") == "core.views.custom_server_error"
