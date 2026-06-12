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
