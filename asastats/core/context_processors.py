"""Inject this deployment's backend capabilities (Gate A) into every template."""

import logging

from django.conf import settings
from django.core.cache import cache

from api.client import BackendError, fetch_capabilities

logger = logging.getLogger(__name__)
_CACHE_KEY = "deployment_capabilities"
_CACHE_TTL = 300  # seconds; tier changes take effect within this window


def deployment_capabilities(request):
    """Return {"deployment_capabilities": {"permission": <int>, ...}}.

    Cached briefly so we don't hit the backend on every request. On failure we
    return a zero-permission stub so gated links simply don't render.
    """
    caps = cache.get(_CACHE_KEY)
    if caps is None:
        try:
            caps = fetch_capabilities()

        except (BackendError, Exception):  # noqa: BLE001 - never break rendering
            logger.warning("Could not fetch deployment capabilities", exc_info=True)
            caps = {"permission": 0}

        cache.set(_CACHE_KEY, caps, _CACHE_TTL)

    return {"deployment_capabilities": caps}


def walletconnect(request):
    """Expose the WalletConnect project id to template context.

    :param request: current request (unused; signature required by Django)
    :type request: django.http.HttpRequest
    :return: mapping with the WalletConnect project id
    :rtype: dict
    """
    return {
        "WALLETCONNECT_PROJECT_ID": getattr(settings, "WALLETCONNECT_PROJECT_ID", "")
    }
