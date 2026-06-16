"""Testing module for core app synchronous url dispatcher module."""

from django.conf import settings
from django.urls import URLPattern

from core import urls
from utils.constants.users import BUNDLENAME_REGEX


class TestCoreUrls:
    """Testing class for :py:mod:`website.core.urls` module."""

    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    def test_core_urls_robots_and_ownership_files(self):
        url = self._url_from_pattern(
            r"^(?P<filename>(robots.txt|{}))$".format(settings.GOOGLE_OWNERSHIP_FILE)
        )
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.index_file"
        assert url.name == "index_file"

    def test_core_urls_html_file(self):
        url = self._url_from_pattern(
            r"^(?P<filename>(auth_privacy\.html|auth_terms\.html))$"
        )
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.html_file"
        assert url.name == "html_file"

    def test_core_urls_assets_files(self):
        url = self._url_from_pattern(
            r"^(?P<suffix>(asastats.png|asastats-dark.png|colors.png|icon.png"
            "|logo.png|logo-dark.png|logo.svg|logo400.png|whitepaper.pdf"
            "|transparency-report-202[1-6]-(?:1[012]|0?[1-9]).pdf))$",
        )
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.assets_file"
        assert url.name == "assets_file"

    def test_core_urls_social_icons(self):
        url = self._url_from_pattern(
            r"^(?P<suffix>(discord24.png|twitter24.png|reddit24.png|github24.png))$"
        )
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.social_icons"
        assert url.name == "social_icons"

    def test_core_urls_index(self):
        url = self._url_from_pattern(r"^$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.IndexView"
        assert url.name == "index"

    def test_core_urls_home(self):
        url = self._url_from_pattern(r"^home/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.HomePageView"
        assert url.name == "home"

    def test_core_urls_profile(self):
        url = self._url_from_pattern(r"^profile/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfileEditView"
        assert url.name == "profile"

    def test_core_urls_profile_account(self):
        url = self._url_from_pattern(r"^profile/account/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfileAccountView"
        assert url.name == "profile_account"

    def test_core_urls_profile_deactivate(self):
        url = self._url_from_pattern(r"^profile/deactivate/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.DeactivateProfileView"
        assert url.name == "deactivate_profile"

    def test_core_urls_profile_api(self):
        url = self._url_from_pattern(r"^profile/api/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfileApiView"
        assert url.name == "profile_api"

    def test_core_urls_profile_authorize(self):
        url = self._url_from_pattern(r"^profile/authorize/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfileAuthorizeView"
        assert url.name == "profile_authorize"

    def test_core_urls_profile_authorize_check(self):
        url = self._url_from_pattern(r"^profile/authorize/check/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfileAuthorizeCheckView"
        assert url.name == "profile_authorize_check"

    def test_core_urls_profile_connected_addresses(self):
        url = self._url_from_pattern(r"^profile/addresses/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfileAddressesView"
        assert url.name == "profile_addresses"

    def test_core_urls_profile_link_address(self):
        url = self._url_from_pattern(r"^profile/addresses/link/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfileLinkAddressView"
        assert url.name == "profile_link_address"

    def test_core_urls_profile_permission_fetch(self):
        url = self._url_from_pattern(r"^profile/permission/fetch/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ProfilePermissionFetchView"
        assert url.name == "profile_permission_fetch"

    def test_core_urls_profile_add_bundlename(self):
        url = self._url_from_pattern(r"^profile/add-bundle$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.BundleNameAddView"
        assert url.name == "bundlename_add"

    def test_core_urls_profile_delete_bundlename(self):
        url = self._url_from_pattern(r"^profile/{}/delete/$".format(BUNDLENAME_REGEX))
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.BundleNameDeleteView"
        assert url.name == "bundlename_delete"

    def test_core_urls_profile_edit_bundlename(self):
        url = self._url_from_pattern(r"^profile/{}/$".format(BUNDLENAME_REGEX))
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.BundleNameEditView"
        assert url.name == "bundlename_edit"

    def test_core_urls_customaddress(self):
        url = self._url_from_pattern(
            r"^(MVEKYHFLJ63UKDYGNKCJD7WO5KFJZFVFMJPSDAWLDIDP4LUP575YDOW6GI)$"
        )
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.AddressViewCustom"
        assert url.name == "custom_address1"

    def test_core_urls_address(self):
        url = self._url_from_pattern(r"^([0-9A-Za-z]{58})$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.AddressView"
        assert url.name == "address"

    def test_core_urls_bundle(self):
        url = self._url_from_pattern(r"^([0-9A-Za-z]{40})$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.AddressView"
        assert url.name == "bundle"

    def test_core_urls_ans(self):
        url = self._url_from_pattern(r"^([-\w]+\.(algo|Algo|ALGO))/(ans|Ans|ANS)$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.AnsView"
        assert url.name == "ans"

    def test_core_urls_nfd(self):
        url = self._url_from_pattern(
            r"^([-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/(nfd|Nfd|NFD)$"
        )
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.NfdView"
        assert url.name == "nfd"

    def test_core_urls_name_service(self):
        url = self._url_from_pattern(r"^([-\w]*\.*[-\w]+\.(algo|Algo|ALGO))$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.NameServiceView"
        assert url.name == "name_service"

    def test_core_urls_about(self):
        url = self._url_from_pattern(r"^about/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.AboutView"
        assert url.name == "about"

    def test_core_urls_tokenomics(self):
        url = self._url_from_pattern(r"^tokenomics/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.TokenomicsView"
        assert url.name == "tokenomics"

    def test_core_urls_faq(self):
        url = self._url_from_pattern(r"^faq/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.FaqView"
        assert url.name == "faq"

    def test_core_urls_features(self):
        url = self._url_from_pattern(r"^features/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.FeaturesView"
        assert url.name == "features"

    def test_core_urls_subscriptions(self):
        url = self._url_from_pattern(r"^subscriptions/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.SubscriptionsView"
        assert url.name == "subscriptions"

    def test_core_urls_disclaimer(self):
        url = self._url_from_pattern(r"^disclaimer/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.DisclaimerView"
        assert url.name == "disclaimer"

    def test_core_urls_asm_privacy(self):
        url = self._url_from_pattern(r"^asm-privacy/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ASMPrivacyView"
        assert url.name == "asm_privacy"

    def test_core_urls_export_address(self):
        url = self._url_from_pattern(r"^export/([0-9A-Za-z]{58})/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ExportView"
        assert url.name == "export_address"

    def test_core_urls_export_bundle(self):
        url = self._url_from_pattern(r"^export/([0-9A-Za-z]{40})/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.ExportView"
        assert url.name == "export_bundle"

    def test_core_urls_export_download(self):
        url = self._url_from_pattern(r"^export/download/$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.export_download"
        assert url.name == "export_download"

    def test_core_urls_bundle_name(self):
        url = self._url_from_pattern(r"^([\.\w\s-]{1,50})$")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "core.views.BundleNameView"
        assert url.name == "bundle_name"

    def test_core_urls_patterns_count(self):
        assert len(urls.urlpatterns) == 35
