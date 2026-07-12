"""Module containing core app's custom middlewares."""

from django.conf import settings
from django_minify_html.middleware import MinifyHtmlMiddleware

from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS


class CustomMinifyHtmlMiddleware(MinifyHtmlMiddleware):
    """Custom configuration for django-minify-html middleware."""

    minify_args = MinifyHtmlMiddleware.minify_args | {
        "minify_css": False,
        "minify_js": False,
        "minify_doctype": False,
        "allow_removing_spaces_between_attributes": False,
        "allow_noncompliant_unquoted_attribute_values": False,
        "keep_closing_tags": True,
    }


class CustomUserHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        header = "user"
        if (
            request.user.is_authenticated
            and request.user.profile
            and request.user.profile.permission
            >= SUBSCRIPTION_TIER_PERMISSIONS.get("Intro")
        ):
            header = "other"

        response["X-User-Header"] = header
        return response


class DebugEnvMiddleware:
    """Stamp every response with which settings/session/cache the *serving*
    process actually loaded. Compare a normal page (WSGI) with a /widgets/…
    request (Daphne): any difference in SESSION or CACHE is the bug.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        cache_default = settings.CACHES.get("default", {})
        response["X-Debug-Env"] = (
            f"MODULE={getattr(settings, 'SETTINGS_MODULE', 'None')} | "
            f"SESSION={getattr(settings, 'SESSION_ENGINE', 'None')} | "
            f"CACHE_BACKEND={cache_default.get('BACKEND', 'None')} | "
            f"CACHE_LOC={cache_default.get('LOCATION', 'None')} | "
            f"CACHE_PFX={cache_default.get('KEY_PREFIX', 'None')} | "
            f"AUTH={request.user.is_authenticated}"
        )
        response["X-Debug-Cookie"] = request.META.get("HTTP_COOKIE", "MISSING")[:80]

        from django.core.cache import cache

        probe = f"probe:{request.META.get('HTTP_HOST','')}"
        cache.set(probe, "seen", 30)
        response["X-Debug-Cache-Probe"] = (
            f"{probe}={cache.get(probe)} | id={id(cache._cache) if hasattr(cache,'_cache') else 'na'}"
        )
        # also surface the raw session lookup:
        from importlib import import_module

        engine = import_module(settings.SESSION_ENGINE)
        sk = request.COOKIES.get("sessionid", "")
        s = engine.SessionStore(sk)
        response["X-Debug-Session"] = (
            f"key={sk[:6]} exists={s.exists(sk) if sk else 'no-key'} keys={list(s.keys())}"
        )

        import hashlib
        response["X-Debug-Secret"] = hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()[:12]

        return response
