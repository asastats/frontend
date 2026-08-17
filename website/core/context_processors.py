"""Inject this deployment's backend capabilities (Gate A) into every template."""

import json
import logging
from pathlib import Path

from django.conf import settings
from django.core.cache import cache

from api.client import BackendError, fetch_capabilities

logger = logging.getLogger(__name__)

#: Written by build-typefaces.py beside the stylesheet it generates, so the
#: pairings offered and the CSS backing them come from one run.
_TYPEFACES_PATH = Path(settings.STATICFILES_DIRS[0]) / "css" / "typefaces.json"
_TYPEFACES_CACHE = None

_CACHE_KEY = "deployment_capabilities"
_CACHE_TTL = 300  # seconds; tier changes take effect within this window

#: The primary navigation, in the order it is shown. Entries are url names so
#: the header can mark the active one by comparing against the resolved url --
#: no page has to declare where it is.
#:
#: Two lists, because the row is short and what belongs in it depends entirely
#: on who is reading. A signed-in reader wants their portfolio and a way out; a
#: signed-out one wants a way in and a reason to stay. Offering Home to someone
#: who cannot use it, or Subscriptions to someone who already subscribes, is
#: what padding this row to a single fixed list costs.
#:
#: Everything not here is still reachable from the footer, which is the full
#: map. This row is the short list, not the sitemap.
MAIN_NAVIGATION_AUTHENTICATED = [
    ("home", "Home"),
    ("swagger-ui", "API"),
    ("account_logout", "Log out"),
]

MAIN_NAVIGATION_ANONYMOUS = [
    ("swagger-ui", "API"),
    ("subscriptions", "Subscriptions"),
]

#: The profile section's sub-navigation, in the order it is shown. Rendered by
#: base_profile.html, so adding a page there is a change here and nowhere else.
PROFILE_SECTIONS = [
    ("profile", "Profile"),
    ("profile_account", "Account"),
    ("profile_api", "API token"),
    ("profile_addresses", "Addresses"),
    ("profile_settings", "Settings"),
    ("profile_appearance", "Appearance"),
]


def load_typefaces():
    """Return {theme: {display, sans, mono}}, read once per process.

    Read from disk rather than imported: the file is build output, and a
    missing or unreadable one must degrade to "no typefaces offered" rather
    than take every page down with it.

    :return: dict
    """
    global _TYPEFACES_CACHE
    if _TYPEFACES_CACHE is None:
        try:
            _TYPEFACES_CACHE = json.loads(_TYPEFACES_PATH.read_text())
        except (OSError, ValueError):
            logger.warning("Could not read %s", _TYPEFACES_PATH, exc_info=True)
            _TYPEFACES_CACHE = {}
    return _TYPEFACES_CACHE


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


def main_navigation(request):
    """Return the primary navigation for base.html.

    The signed-out list has no Log in entry: logging in opens a dialog rather
    than navigating anywhere, so it has no url name to reverse and the header
    renders it itself, ahead of these.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: dict
    """
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return {"main_navigation": MAIN_NAVIGATION_AUTHENTICATED}

    return {"main_navigation": MAIN_NAVIGATION_ANONYMOUS}


def profile_navigation(request):
    """Return the profile sub-navigation for base_profile.html.

    A context processor rather than a per-view context entry: every page in
    the section renders the same nav, and five views each building their own
    copy is five chances for them to disagree about the order or a label.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: dict
    """
    return {"profile_sections": PROFILE_SECTIONS}


def global_constants(request):
    """Return collection of project's constants.

    :param request: HTTP request object
    :type request: :class:`django.http.HttpRequest`
    :return: dict
    """
    return {
        "WEBSITE_NAME": settings.WEBSITE_NAME,
        "WEBSITE_SHORT_NAME": settings.WEBSITE_SHORT_NAME,
        "WEBSITE_URL": settings.WEBSITE_URL,
        "WEBSITE_DOMAIN": settings.WEBSITE_DOMAIN,
        "BASE_CDN_URL": settings.BASE_CDN_URL,
        "X_HANDLE": settings.X_HANDLE,
        "SUBREDDIT_NAME": settings.SUBREDDIT_NAME,
        "ANDROID_APP": settings.ANDROID_APP,
        "IOS_APP": settings.IOS_APP,
        "MEDIUM_NAME": settings.MEDIUM_NAME,
        "DISCORD_INVITE": settings.DISCORD_INVITE,
        "GITHUB_ORGANIZATION": settings.GITHUB_ORGANIZATION,
        "AVAILABLE_THEMES": settings.AVAILABLE_THEMES,
        "AVAILABLE_THEMES_BY_SCHEME": settings.AVAILABLE_THEMES_BY_SCHEME,
        # The pair the signed-out light/dark switch flips between.
        "BRAND_THEME_LIGHT": settings.BRAND_THEME_LIGHT,
        "BRAND_THEME_DARK": settings.BRAND_THEME_DARK,
        # Named in the picker. Several themes are third-party and
        # CC BY 4.0, which makes the credit a licence condition.
        "THEME_ATTRIBUTION": settings.THEME_ATTRIBUTION,
    }


def walletconnect(request):
    """Expose the WalletConnect project id to template context.

    :param request: current request (unused; signature required by Django)
    :type request: django.http.HttpRequest
    :return: mapping with the WalletConnect project id
    :rtype: dict
    """
    return {
        "WALLET_CONNECT_PROJECT_ID": getattr(settings, "WALLET_CONNECT_PROJECT_ID", "")
    }
