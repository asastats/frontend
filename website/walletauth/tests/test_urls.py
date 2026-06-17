"""Testing module for :py:mod:`walletauth.urls` module."""

from django.urls import URLPattern

from walletauth import urls


class TestWalletauthUrls:
    """Testing class for :py:mod:`walletauth.urls` module."""

    # # HELPERS
    def _url_from_pattern(self, pattern):
        return next(url for url in urls.urlpatterns if str(url.pattern) == pattern)

    # # urlpatterns
    def test_walletauth_urls_wallets(self):
        url = self._url_from_pattern("wallets/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletsAPIView"
        assert url.name == "wallet_wallets"

    def test_walletauth_urls_nonce(self):
        url = self._url_from_pattern("nonce/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletNonceAPIView"
        assert url.name == "wallet_nonce"

    def test_walletauth_urls_verify(self):
        url = self._url_from_pattern("verify/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletVerifyAPIView"
        assert url.name == "wallet_verify"

    def test_walletauth_urls_login_wallets(self):
        url = self._url_from_pattern("login/wallets/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletsAPIView"
        assert url.name == "wallet_login_wallets"

    def test_walletauth_urls_login_nonce(self):
        url = self._url_from_pattern("login/nonce/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.login_views.WalletLoginNonceAPIView"
        assert url.name == "wallet_login_nonce"

    def test_walletauth_urls_login_verify(self):
        url = self._url_from_pattern("login/verify/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.login_views.WalletLoginVerifyAPIView"
        assert url.name == "wallet_login_verify"

    def test_walletauth_urls_link_nonce(self):
        url = self._url_from_pattern("link/nonce/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.link_views.WalletLinkNonceAPIView"
        assert url.name == "wallet_link_nonce"

    def test_walletauth_urls_link_verify(self):
        url = self._url_from_pattern("link/verify/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.link_views.WalletLinkVerifyAPIView"
        assert url.name == "wallet_link_verify"

    def test_walletauth_urls_link_wallets(self):
        url = self._url_from_pattern("link/wallets/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.views.WalletsAPIView"
        assert url.name == "wallet_link_wallets"

    def test_walletauth_urls_manage_nonce(self):
        url = self._url_from_pattern("manage/nonce/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.management_views.ManageNonceAPIView"
        assert url.name == "wallet_manage_nonce"

    def test_walletauth_urls_swap_gate(self):
        url = self._url_from_pattern("gate/")
        assert isinstance(url, URLPattern)
        assert url.lookup_str == "walletauth.gating_views.SwapGateAPIView"
        assert url.name == "wallet_swap_gate"
