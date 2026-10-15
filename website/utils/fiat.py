"""Module with the reader's fiat currency and its latest rate from USD."""

import json
import logging
import time

from django.conf import settings

from utils.clients import redis_instance

logger = logging.getLogger(__name__)

#: Written by the engine's `pricer.fiat.publish_latest`; the name is shared with it.
CACHE_KEY_FIAT_RATES = "fxrt"
FIAT_RATES_MEMO_SECONDS = 300
FIAT_SYMBOLS = {"USD": "$", "EUR": "€"}
USD_FIAT = {"code": "USD", "rate": 1.0, "symbol": "$"}

_memo = {"at": None, "rates": {}}


def latest_rates(client=None, now=None):
    """Return the latest rate per fiat code from USD, re-read every five minutes.

    A failed read keeps the rates read last.

    :param client: the frontend's Redis client
    :type client: :class:`Redis`
    :param now: monotonic seconds, for tests
    :type now: float
    :var raw: JSON published by the engine
    :type raw: bytes
    :return: dict
    """
    now = time.monotonic() if now is None else now
    if _memo["at"] is not None and now - _memo["at"] < FIAT_RATES_MEMO_SECONDS:
        return _memo["rates"]

    try:
        raw = (client or redis_instance()).get(CACHE_KEY_FIAT_RATES)
        rates = (
            {code: float(entry["rate"]) for code, entry in json.loads(raw).items()}
            if raw
            else {}
        )
    except Exception as error:  # noqa: BLE001 - USD is always a safe answer
        logger.warning("fiat rates unreadable: %s", error)
        rates = _memo["rates"]

    _memo.update(at=now, rates=rates)
    return rates


def fiat_for_user(user):
    """Return the code, rate from USD and symbol of the fiat `user` sees.

    USD for anonymous readers, for unknown codes and when the rate is missing.

    :param user: request's user
    :type user: :class:`User`
    :var code: chosen fiat code
    :type code: str
    :return: dict
    """
    try:
        code = user.profile.fiat if user.is_authenticated else "USD"
    except Exception:  # noqa: BLE001 - a user without a profile reads USD
        code = "USD"

    if code == "USD" or code not in settings.FIAT_CURRENCIES:
        return dict(USD_FIAT)

    rate = latest_rates().get(code)
    if not rate:
        return dict(USD_FIAT)

    return {"code": code, "rate": rate, "symbol": FIAT_SYMBOLS.get(code, "")}
