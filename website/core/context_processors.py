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


#: The primary navigation, in the order it is shown. Entries are url names so
#: the header can mark the active one by comparing against the resolved url --
#: no page has to declare where it is.
MAIN_NAVIGATION = [
    ("home", "Home"),
    ("features", "Features"),
    ("subscriptions", "Subscriptions"),
    ("swagger-ui", "API"),
    ("faq", "FAQ"),
]


def main_navigation(request):
    """Return the primary navigation for base.html.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: dict
    """
    return {"main_navigation": MAIN_NAVIGATION}


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
