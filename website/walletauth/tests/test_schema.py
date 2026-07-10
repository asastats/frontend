"""Testing module for :py:mod:`walletauth.schema` module."""

from walletauth.schema import exclude_wallet_endpoints


class TestWalletauthSchema:
    """Testing class for :py:mod:`walletauth.schema`."""

    def test_walletauth_schema_exclude_wallet_endpoints_drops_wallet_paths(self):
        endpoints = [
            ("/api/v2/wallet/login/verify/", "re1", "POST", object()),
            ("/api/v2/wallet/nonce/", "re2", "POST", object()),
            ("/api/v2/accounts/", "re3", "GET", object()),
            ("/home/", "re4", "GET", object()),
        ]
        kept = exclude_wallet_endpoints(endpoints)
        assert [endpoint[0] for endpoint in kept] == ["/api/v2/accounts/", "/home/"]

    def test_walletauth_schema_exclude_wallet_endpoints_preserves_non_wallet_tuple(
        self,
    ):
        callback = object()
        endpoints = [("/api/v2/accounts/", "regex", "GET", callback)]
        assert exclude_wallet_endpoints(endpoints) == [
            ("/api/v2/accounts/", "regex", "GET", callback)
        ]

    def test_walletauth_schema_exclude_wallet_endpoints_returns_empty_for_empty(self):
        assert exclude_wallet_endpoints([]) == []

    def test_walletauth_schema_exclude_wallet_endpoints_keeps_lookalike_prefix(self):
        # A path that merely contains, but does not start with, the wallet prefix
        # is not excluded.
        endpoints = [("/api/v2/other/api/v2/wallet/x/", "re", "GET", object())]
        assert exclude_wallet_endpoints(endpoints) == endpoints

    def test_walletauth_schema_exclude_wallet_endpoints_accepts_generator_kwargs(self):
        # drf-spectacular invokes preprocessing hooks with extra kwargs.
        endpoints = [("/api/v2/wallet/gate/", "re", "GET", object())]
        assert exclude_wallet_endpoints(endpoints, generator=None, request=None) == []
