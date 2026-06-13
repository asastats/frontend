"""Testing module for :py:mod:`walletauth.throttling` module."""

from rest_framework.throttling import UserRateThrottle

from walletauth.throttling import WalletAuthRateThrottle


class TestWalletAuthRateThrottle:
    """Testing class for :class:`WalletAuthRateThrottle` throttle."""

    # # configuration
    def test_walletauth_throttle_is_user_rate_throttle(self):
        assert issubclass(WalletAuthRateThrottle, UserRateThrottle)

    def test_walletauth_throttle_scope(self):
        assert WalletAuthRateThrottle.scope == "walletauth"

    # # get_rate
    def test_walletauth_throttle_rate_none_when_unconfigured(self, mocker):
        mocker.patch.object(WalletAuthRateThrottle, "THROTTLE_RATES", {})
        assert WalletAuthRateThrottle().get_rate() is None

    def test_walletauth_throttle_rate_from_settings(self, mocker):
        mocker.patch.object(
            WalletAuthRateThrottle, "THROTTLE_RATES", {"walletauth": "30/min"}
        )
        assert WalletAuthRateThrottle().get_rate() == "30/min"
