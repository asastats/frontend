"""Testing module for :py:mod:`walletauth.templatetags.walletauth_extras`."""

from core.tests.test_appclient import ANDROID_UA, BROWSER_UA, _request
from utils.constants.core import ALGORAND_WALLETS
from walletauth.templatetags.walletauth_extras import supported_wallets


class TestSupportedWallets:
    """Testing class for the :func:`supported_wallets` template tag."""

    # # supported_wallets
    def test_supported_wallets_returns_every_wallet_in_a_browser(self):
        assert supported_wallets({"request": _request(BROWSER_UA)}) == ALGORAND_WALLETS

    def test_supported_wallets_drops_extension_wallets_in_the_app(self):
        ids = [
            wallet["id"]
            for wallet in supported_wallets({"request": _request(ANDROID_UA)})
        ]

        assert ids == ["pera", "defly"]
