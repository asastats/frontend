"""Testing module for :py:mod:`walletauth.throttling` module."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from walletauth.throttling import WalletAuthRateThrottle, WalletLoginRateThrottle


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


class TestWalletLoginRateThrottle:
    """Testing class for :class:`WalletLoginRateThrottle` throttle."""

    # # configuration
    def test_login_throttle_is_anon_rate_throttle(self):
        assert issubclass(WalletLoginRateThrottle, AnonRateThrottle)

    def test_login_throttle_scope(self):
        assert WalletLoginRateThrottle.scope == "walletauth-login"

    # # get_rate
    def test_login_throttle_rate_none_when_unconfigured(self, mocker):
        mocker.patch.object(WalletLoginRateThrottle, "THROTTLE_RATES", {})
        assert WalletLoginRateThrottle().get_rate() is None

    def test_login_throttle_rate_from_settings(self, mocker):
        mocker.patch.object(
            WalletLoginRateThrottle, "THROTTLE_RATES", {"walletauth-login": "10/min"}
        )
        assert WalletLoginRateThrottle().get_rate() == "10/min"
