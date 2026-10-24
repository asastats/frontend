"""Recognise requests made by the ASA Stats app and what it may be shown.

The only place that parses the app's user-agent token; see docs/logbook.md.
"""

import re
from dataclasses import dataclass

from django.conf import settings

#: Shown in the app where a browser gets a link towards buying or upgrading.
PURCHASE_HIDDEN_TEXT = "Not included in your current plan."

#: Appended by mobile/capacitor.config.ts: change both together.
APP_CLIENT_REGEX = re.compile(r"\bASAStatsApp/(\d+)\.(\d+)\.(\d+) \((ios|android)\)")


@dataclass(frozen=True)
class AppClient:
    """The app a request came from.

    :param platform: ``"ios"`` or ``"android"``
    :type platform: str
    :param version: app version as ``(major, minor, patch)``
    :type version: tuple
    """

    platform: str
    version: tuple

    @property
    def version_string(self):
        """Return the version as written in the token, e.g. ``"1.1.0"``.

        :return: str
        """
        return ".".join(str(part) for part in self.version)


def parse_app_client(user_agent):
    """Return the :class:`AppClient` named in `user_agent`, or None.

    :param user_agent: value of the User-Agent header
    :type user_agent: str
    :return: :class:`AppClient` or None
    """
    match = APP_CLIENT_REGEX.search(user_agent or "")
    if match is None:
        return None

    major, minor, patch, platform = match.groups()
    return AppClient(platform=platform, version=(int(major), int(minor), int(patch)))


def app_client(request):
    """Return the request's :class:`AppClient`, or None for a browser.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`AppClient` or None
    """
    return getattr(request, "app_client", None)


def app_cache_prefix(request):
    """Return a ``cache_page`` key prefix that keeps app pages apart.

    None for a browser, so browser cache keys are what they were before the app.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: str or None
    """
    client = app_client(request)
    return None if client is None else f"app-{client.platform}"


def purchase_hidden(request):
    """Return True if calls to buy or upgrade must not be shown to `request`.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: bool
    """
    client = app_client(request)
    return client is not None and client.platform in settings.APP_HIDE_PURCHASE


def widget_hidden(request, name):
    """Return True if the widget called `name` is switched off for `request`.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param name: widget name, as in ``settings.INHOUSE_WIDGETS``
    :type name: str
    :return: bool
    """
    client = app_client(request)
    if client is None:
        return False

    return name in settings.APP_HIDDEN_WIDGETS.get(client.platform, frozenset())


def wallet_supported(request, wallet_id):
    """Return True if the wallet `wallet_id` can be used from `request`.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param wallet_id: wallet id, as in ``ALGORAND_WALLETS``
    :type wallet_id: str
    :return: bool
    """
    return app_client(request) is None or wallet_id not in settings.APP_UNSUPPORTED_WALLETS
