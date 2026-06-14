"""Testing module for :py:mod:`walletauth.templatetags.walletauth_extras`."""

from utils.constants.core import ALGORAND_WALLETS
from walletauth.templatetags.walletauth_extras import supported_wallets


class TestSupportedWallets:
    """Testing class for the :func:`supported_wallets` template tag."""

    # # supported_wallets
    def test_supported_wallets_returns_descriptors(self):
        assert supported_wallets() == ALGORAND_WALLETS
