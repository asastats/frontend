"""Testing module for aqpi app synchronous url dispatcher module."""

from django.urls import URLPattern, URLResolver

from api import urls


class TestApiUrls:
    """Testing class for :py:mod:`website.api.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    def _url_from_pattern_list(self, pattern):
        return next(
            url
            for url in urls.urlpatterns
            if isinstance(url, URLResolver) and str(url.pattern) == pattern
        )

    def test_api_urls_api_raw(self):
        url = self._url_from_pattern(r"$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "api.views.RawPostView"
        assert url.name == "api_v2_raw"

    def test_api_urls_api_address(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(url for url in root_url.url_patterns if url.name == "api_v2_address")
        assert str(url.pattern) == ""
        assert url.lookup_str == "api.views.AddressView"
        assert url.default_args == {}

    def test_api_urls_api_address_asas(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url for url in root_url.url_patterns if url.name == "api_v2_address_asas"
        )
        assert str(url.pattern) == "asas/"
        assert url.lookup_str == "api.views.AddressViewAsas"
        assert url.default_args == {"id": True}

    def test_api_urls_api_address_asas_asset(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_address_asas_asset"
        )
        assert str(url.pattern) == "asas/<int:id>/"
        assert url.lookup_str == "api.views.AddressViewAsasAsset"
        assert url.default_args == {}

    def test_api_urls_api_address_nfts(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url for url in root_url.url_patterns if url.name == "api_v2_address_nfts"
        )
        assert str(url.pattern) == "nfts/"
        assert url.lookup_str == "api.views.AddressViewNfts"
        assert url.default_args == {"id": True}

    def test_api_urls_api_address_nfts_asset(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_address_nfts_asset"
        )
        assert str(url.pattern) == "nfts/<int:id>/"
        assert url.lookup_str == "api.views.AddressViewNftsAsset"
        assert url.default_args == {}

    def test_api_urls_api_address_nftcollections(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_address_nftcollections"
        )
        assert str(url.pattern) == "nftcollections/"
        assert url.lookup_str == "api.views.AddressViewNftCollections"
        assert url.default_args == {"name": True}

    def test_api_urls_api_address_nftcollections_asset(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_address_nftcollections_collection"
        )
        assert str(url.pattern) == "nftcollections/<str:name>/"
        assert url.lookup_str == "api.views.AddressViewNftCollectionsCollection"
        assert url.default_args == {}

    def test_api_urls_api_address_entities(self):
        root_pattern = r"(?P<address>[0-9A-Za-z]{58})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_address_entities"
        )
        assert str(url.pattern) == "entities/"
        assert url.lookup_str == "api.views.AddressEntities"
        assert url.default_args == {}

    def test_api_urls_api_bundle(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(url for url in root_url.url_patterns if url.name == "api_v2_bundle")
        assert url.lookup_str == "api.views.BundleView"
        assert url.default_args == {}

    def test_api_urls_api_bundle_asas(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url for url in root_url.url_patterns if url.name == "api_v2_bundle_asas"
        )
        assert str(url.pattern) == "asas/"
        assert url.lookup_str == "api.views.BundleViewAsas"
        assert url.default_args == {"id": True}

    def test_api_urls_api_bundle_asas_asset(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_bundle_asas_asset"
        )
        assert str(url.pattern) == "asas/<int:id>/"
        assert url.lookup_str == "api.views.BundleViewAsasAsset"
        assert url.default_args == {}

    def test_api_urls_api_bundle_nfts(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url for url in root_url.url_patterns if url.name == "api_v2_bundle_nfts"
        )
        assert str(url.pattern) == "nfts/"
        assert url.lookup_str == "api.views.BundleViewNfts"
        assert url.default_args == {"id": True}

    def test_api_urls_api_bundle_nfts_asset(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_bundle_nfts_asset"
        )
        assert str(url.pattern) == "nfts/<int:id>/"
        assert url.lookup_str == "api.views.BundleViewNftsAsset"
        assert url.default_args == {}

    def test_api_urls_api_bundle_nftcollections(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_bundle_nftcollections"
        )
        assert str(url.pattern) == "nftcollections/"
        assert url.lookup_str == "api.views.BundleViewNftCollections"
        assert url.default_args == {"name": True}

    def test_api_urls_api_bundle_nftcollections_collection(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_bundle_nftcollections_collection"
        )
        assert str(url.pattern) == "nftcollections/<str:name>/"
        assert url.lookup_str == "api.views.BundleViewNftCollectionsCollection"
        assert url.default_args == {}

    def test_api_urls_api_bundle_entities(self):
        root_pattern = r"(?P<bundle>[0-9A-Za-z]{40})/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url for url in root_url.url_patterns if url.name == "api_v2_bundle_entities"
        )
        assert str(url.pattern) == "entities/"
        assert url.lookup_str == "api.views.BundleEntities"
        assert url.default_args == {}

    def test_api_urls_api_nfdname(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(url for url in root_url.url_patterns if url.name == "api_v2_nfdname")
        assert url.lookup_str == "api.views.NfdNameView"
        assert url.default_args == {}

    def test_api_urls_api_nfdname_asas(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url for url in root_url.url_patterns if url.name == "api_v2_nfdname_asas"
        )
        assert str(url.pattern) == "asas/"
        assert url.lookup_str == "api.views.NfdNameViewAsas"
        assert url.default_args == {"id": True}

    def test_api_urls_api_nfdname_asas_asset(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_nfdname_asas_asset"
        )
        assert str(url.pattern) == "asas/<int:id>/"
        assert url.lookup_str == "api.views.NfdNameViewAsasAsset"
        assert url.default_args == {}

    def test_api_urls_api_nfdname_nfts(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url for url in root_url.url_patterns if url.name == "api_v2_nfdname_nfts"
        )
        assert str(url.pattern) == "nfts/"
        assert url.lookup_str == "api.views.NfdNameViewNfts"
        assert url.default_args == {"id": True}

    def test_api_urls_api_nfdname_nfts_asset(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_nfdname_nfts_asset"
        )
        assert str(url.pattern) == "nfts/<int:id>/"
        assert url.lookup_str == "api.views.NfdNameViewNftsAsset"
        assert url.default_args == {}

    def test_api_urls_api_nfdname_nftcollections(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_nfdname_nftcollections"
        )
        assert str(url.pattern) == "nftcollections/"
        assert url.lookup_str == "api.views.NfdNameViewNftCollections"
        assert url.default_args == {"name": True}

    def test_api_urls_api_nfdname_nftcollections_collection(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_nfdname_nftcollections_collection"
        )
        assert str(url.pattern) == "nftcollections/<str:name>/"
        assert url.lookup_str == "api.views.NfdNameViewNftCollectionsCollection"
        assert url.default_args == {}

    def test_api_urls_api_nfdname_entities(self):
        root_pattern = r"(?P<nfd_name>[-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/"
        root_url = self._url_from_pattern_list(root_pattern)
        assert isinstance(root_url, URLResolver)
        url = next(
            url
            for url in root_url.url_patterns
            if url.name == "api_v2_nfdname_entities"
        )
        assert str(url.pattern) == "entities/"
        assert url.lookup_str == "api.views.NfdNameEntities"
        assert url.default_args == {}

    def test_api_urls_token_obtain_pair(self):
        url = self._url_from_pattern(r"token/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "rest_framework_simplejwt.views.TokenObtainPairView"
        assert url.name == "token_obtain_pair"

    def test_api_urls_token_refresh(self):
        url = self._url_from_pattern(r"token/refresh/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "rest_framework_simplejwt.views.TokenRefreshView"
        assert url.name == "token_refresh"

    def test_api_urls_openapi_schema(self):
        url = self._url_from_pattern(r"schema/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "drf_spectacular.views.SpectacularAPIView"
        assert url.name == "api_schema"

    def test_api_urls_openapi_swagger_ui(self):
        url = self._url_from_pattern(r"schema/swagger-ui/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "drf_spectacular.views.SpectacularSwaggerView"
        assert url.name == "swagger-ui"

    def test_api_urls_openapi_redoc(self):
        url = self._url_from_pattern(r"schema/redoc/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "drf_spectacular.views.SpectacularRedocView"
        assert url.name == "redoc"

    def test_api_urls_api_settings(self):
        url = self._url_from_pattern("settings/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "api.views.SettingsView"
        assert url.name == "api_v2_settings"

    def test_api_urls_api_bundle_name(self):
        url = self._url_from_pattern(r"(?P<name>[-\w]*\.*[-\w]+)/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "api.views.BundleNameView"
        assert url.name == "api_v2_name"

    def test_api_urls_patterns_count(self):
        assert len(urls.urlpatterns) == 11
