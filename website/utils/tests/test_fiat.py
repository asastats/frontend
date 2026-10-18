"""Testing module for :py:mod:`utils.fiat` module."""

import json

import pytest

from utils import fiat
from utils.fiat import (
    CACHE_KEY_FIAT_RATES,
    FIAT_RATES_MEMO_SECONDS,
    USD_FIAT,
    fiat_code_for_user,
    fiat_for_user,
    latest_rates,
)

PUBLISHED = json.dumps({"EUR": {"rate": 0.8938, "date": "2026-10-13"}}).encode()


@pytest.fixture(autouse=True)
def fresh_memo():
    """Start every test with nothing read."""
    fiat._memo.update(at=None, rates={})
    yield
    fiat._memo.update(at=None, rates={})


def _client(mocker, value=PUBLISHED):
    client = mocker.MagicMock()
    client.get.return_value = value
    return client


def _user(mocker, code="EUR", authenticated=True):
    user = mocker.MagicMock()
    user.is_authenticated = authenticated
    user.profile.fiat = code
    return user


class TestUtilsFiatLatestRates:
    """Testing class for :py:func:`utils.fiat.latest_rates`."""

    def test_utils_fiat_latest_rates_reads_the_engine_key(self, mocker):
        client = _client(mocker)
        assert latest_rates(client, now=100.0) == {"EUR": 0.8938}
        client.get.assert_called_once_with(CACHE_KEY_FIAT_RATES)

    def test_utils_fiat_latest_rates_reads_once_per_period(self, mocker):
        client = _client(mocker)
        latest_rates(client, now=100.0)
        latest_rates(client, now=100.0 + FIAT_RATES_MEMO_SECONDS - 1)
        assert client.get.call_count == 1
        latest_rates(client, now=100.0 + FIAT_RATES_MEMO_SECONDS)
        assert client.get.call_count == 2

    def test_utils_fiat_latest_rates_empty_without_the_key(self, mocker):
        assert latest_rates(_client(mocker, None), now=100.0) == {}

    def test_utils_fiat_latest_rates_keeps_the_last_good_read(self, mocker, caplog):
        latest_rates(_client(mocker), now=100.0)
        broken = mocker.MagicMock()
        broken.get.side_effect = ConnectionError("down")
        returned = latest_rates(broken, now=100.0 + FIAT_RATES_MEMO_SECONDS)
        assert returned == {"EUR": 0.8938}
        assert "fiat rates unreadable" in caplog.text

    def test_utils_fiat_latest_rates_survives_bad_json(self, mocker):
        assert latest_rates(_client(mocker, b"{not json"), now=100.0) == {}

    def test_utils_fiat_latest_rates_defaults_to_the_frontend_redis(self, mocker):
        client = _client(mocker)
        mocker.patch("utils.fiat.redis_instance", return_value=client)
        assert latest_rates() == {"EUR": 0.8938}


class TestUtilsFiatForUser:
    """Testing class for :py:func:`utils.fiat.fiat_for_user`."""

    def test_utils_fiat_for_user_eur(self, mocker):
        mocker.patch("utils.fiat.latest_rates", return_value={"EUR": 0.8938})
        assert fiat_for_user(_user(mocker)) == {
            "code": "EUR",
            "rate": 0.8938,
            "symbol": "€",
        }

    def test_utils_fiat_for_user_anonymous_is_usd(self, mocker):
        mocked = mocker.patch("utils.fiat.latest_rates")
        assert fiat_for_user(_user(mocker, authenticated=False)) == USD_FIAT
        mocked.assert_not_called()

    def test_utils_fiat_for_user_usd(self, mocker):
        assert fiat_for_user(_user(mocker, "USD")) == USD_FIAT

    def test_utils_fiat_for_user_without_profile(self, mocker):
        user = mocker.MagicMock(is_authenticated=True)
        type(user).profile = mocker.PropertyMock(side_effect=AttributeError("none"))
        assert fiat_for_user(user) == USD_FIAT

    def test_utils_fiat_for_user_unconfigured_code(self, mocker, settings):
        settings.FIAT_CURRENCIES = ("USD", "EUR")
        assert fiat_for_user(_user(mocker, "GBP")) == USD_FIAT

    def test_utils_fiat_for_user_missing_rate_is_usd(self, mocker):
        mocker.patch("utils.fiat.latest_rates", return_value={})
        assert fiat_for_user(_user(mocker)) == USD_FIAT

    def test_utils_fiat_for_user_code_without_symbol(self, mocker, settings):
        settings.FIAT_CURRENCIES = ("USD", "CHF")
        mocker.patch("utils.fiat.latest_rates", return_value={"CHF": 0.8})
        assert fiat_for_user(_user(mocker, "CHF"))["symbol"] == ""

    def test_utils_fiat_code_for_user_needs_no_rate(self, mocker, settings):
        settings.FIAT_CURRENCIES = ("USD", "EUR")
        rates = mocker.patch("utils.fiat.latest_rates", return_value={})
        assert fiat_code_for_user(_user(mocker)) == "EUR"
        assert fiat_code_for_user(_user(mocker, "GBP")) == "USD"
        assert fiat_code_for_user(None) == "USD"
        rates.assert_not_called()

    def test_utils_fiat_for_user_returns_a_copy(self, mocker):
        fiat_for_user(_user(mocker, "USD"))["code"] = "changed"
        assert USD_FIAT["code"] == "USD"
