"""Native Sign in with Apple and Google in the ASA Stats app (O3).

The flow, the threats and the rejected alternatives are in docs/logbook.md and
capacitor/O3-NATIVE-SIGNIN-DESIGN.md.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

import requests
from django.conf import settings
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.apple import exchange_apple_code
from core.appclient import app_client
from core.views_appauth import AppAuthRedeemThrottle, _message, _safe_next

logger = logging.getLogger(__name__)

#: Providers with a native sheet; mobile/ NativeSignIn checks the same ids.
NATIVE_PROVIDERS = ("apple", "google")
PROCESSES = ("login", "connect")

NONCE_SESSION_KEY = "app_native_nonce"
NONCE_LIFETIME = timedelta(minutes=5)

#: Google signs with either spelling of its issuer.
GOOGLE_ISSUERS = ["https://accounts.google.com", "accounts.google.com"]


class AppAuthNativeThrottle(AppAuthRedeemThrottle):
    """Per-IP limit on native sign-in calls.

    Rate: ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["app-auth-native"]``.
    """

    scope = "app-auth-native"


def nonce_hash(nonce):
    """Return the hex SHA-256 of ``nonce``, as Apple's sheet sends it on.

    :param nonce: the nonce handed to the app
    :type nonce: str
    :return: str
    """
    return hashlib.sha256(nonce.encode()).hexdigest()


def google_audiences():
    """Return the client ids a native Google token may be issued to.

    :return: list
    """
    web = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
    return [client_id for client_id in (web, settings.GOOGLE_IOS_CLIENT_ID) if client_id]


def _require_app(request):
    """Raise 404 unless the request comes from the app.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    """
    if app_client(request) is None:
        raise Http404


def _take_nonce(request):
    """Remove the session's nonce and return its hash while it is fresh.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: str or None
    """
    issued = request.session.pop(NONCE_SESSION_KEY, None)
    if not isinstance(issued, dict):
        return None

    age = timezone.now().timestamp() - issued.get("issued", 0)
    if not 0 <= age <= NONCE_LIFETIME.total_seconds():
        return None

    return issued.get("hash")


def _identity(provider, id_token):
    """Return the verified claims of a native sheet's ID token.

    :param provider: allauth's provider for the token
    :type provider: :class:`allauth.socialaccount.providers.base.Provider`
    :param id_token: the sheet's ID token
    :type id_token: str
    :return: dict
    """
    if provider.id == "apple":
        from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter

        return AppleOAuth2Adapter.get_verified_identity_data(provider, id_token)

    from allauth.socialaccount.internal import jwtkit
    from allauth.socialaccount.providers.google.views import CERTS_URL

    return jwtkit.verify_and_decode(
        credential=id_token,
        keys_url=CERTS_URL,
        issuer=GOOGLE_ISSUERS,
        audience=google_audiences(),
        lookup_kid=jwtkit.lookup_kid_pem_x509_certificate,
    )


def _nonce_matches(provider_id, claims, expected):
    """Return True when the token carries the session's nonce.

    Apple's token carries the hash the app passed to the sheet; Google's the
    nonce itself.

    :param provider_id: ``"apple"`` or ``"google"``
    :type provider_id: str
    :param claims: the token's verified claims
    :type claims: dict
    :param expected: the hash of the nonce this session was given
    :type expected: str
    :return: bool
    """
    claim = claims.get("nonce")
    if not expected or not isinstance(claim, str) or not claim:
        return False

    carried = claim if provider_id == "apple" else nonce_hash(claim)
    return hmac.compare_digest(carried, expected)


def _apple_tokens(request, claims):
    """Add the first-time name to ``claims`` and exchange the sheet's code.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param claims: the token's verified claims, updated in place
    :type claims: dict
    :return: :class:`allauth.socialaccount.models.SocialToken` or None
    """
    from allauth.socialaccount.models import SocialToken

    first = request.POST.get("first_name", "").strip()[:150]
    last = request.POST.get("last_name", "").strip()[:150]
    if first or last:
        claims["name"] = {"firstName": first, "lastName": last}

    code = request.POST.get("code", "")
    tokens = exchange_apple_code(code, settings.APPLE_APP_BUNDLE_ID) if code else None
    if tokens is None:
        return None

    return SocialToken(
        token=tokens.get("access_token", ""), token_secret=tokens["refresh_token"]
    )


@require_POST
def app_native_nonce(request):
    """Give the app a single-use nonce for one native sign-in.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.JsonResponse`
    """
    _require_app(request)
    if not AppAuthNativeThrottle().allow_request(request, None):
        return JsonResponse({"error": "throttled"}, status=429)

    nonce = secrets.token_urlsafe(32)
    request.session[NONCE_SESSION_KEY] = {
        "hash": nonce_hash(nonce),
        "issued": timezone.now().timestamp(),
    }
    response = JsonResponse(
        {
            "nonce": nonce,
            # Android asks Google with the website's client as server client id.
            "google_client_id": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"][
                "client_id"
            ],
        }
    )
    response["Cache-Control"] = "no-store"
    return response


@require_POST
def app_native_signin(request):
    """Sign the WebView's session in, or connect, with a native ID token.

    Every refusal answers the same page and status.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.HttpResponse`
    """
    _require_app(request)
    if not AppAuthNativeThrottle().allow_request(request, None):
        return _message(request, "throttled", 429)

    provider_id = request.POST.get("provider", "")
    process = request.POST.get("process", "login")
    expected = _take_nonce(request)
    if (
        provider_id not in NATIVE_PROVIDERS
        or (provider_id == "apple" and not settings.APPLE_SIGN_IN_ENABLED)
        or process not in PROCESSES
        or (process == "connect" and not request.user.is_authenticated)
    ):
        logger.info("Native sign-in refused: bad request")
        return _message(request, "failed", 400)

    from allauth.socialaccount.adapter import get_adapter
    from allauth.socialaccount.helpers import complete_social_login
    from allauth.socialaccount.providers.oauth2.client import OAuth2Error

    provider = get_adapter().get_provider(request, provider_id)
    try:
        claims = _identity(provider, request.POST.get("id_token", ""))
    except (OAuth2Error, requests.RequestException) as error:
        logger.info("Native sign-in refused: %s", error)
        return _message(request, "failed", 400)

    if not _nonce_matches(provider_id, claims, expected):
        logger.info("Native sign-in refused: nonce")
        return _message(request, "failed", 400)

    token = None
    if provider_id == "apple":
        token = _apple_tokens(request, claims)
        if token is None:
            return _message(request, "failed", 400)

    sociallogin = provider.sociallogin_from_response(request, claims)
    sociallogin.token = token
    if token is not None:
        sociallogin.state["apple_client_id"] = settings.APPLE_APP_BUNDLE_ID
    sociallogin.state["process"] = process
    sociallogin.state["next"] = (
        reverse("socialaccount_connections")
        if process == "connect"
        else _safe_next(request, request.POST.get("next"))
    )
    return complete_social_login(request, sociallogin)
