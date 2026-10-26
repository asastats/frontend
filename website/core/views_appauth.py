"""System-browser sign-in for the ASA Stats app: a one-time ticket (F4).

The flow, the threats and the rejected alternatives are in docs/logbook.md and
capacitor/F4-DESIGN.md.
"""

import base64
import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST
from rest_framework.throttling import SimpleRateThrottle

from core.models import AppLoginTicket

logger = logging.getLogger(__name__)

#: allauth provider ids with a sign-in button, and their names; mobile/ WebAuth
#: checks the same ids.
PROVIDERS = {
    "apple": "Apple",
    "discord": "Discord",
    "github": "GitHub",
    "google": "Google",
    "reddit": "Reddit",
    "twitter_oauth2": "X",
}

#: base64url SHA-256 without padding, as app.js and the WebAuth plugin make it.
CHALLENGE_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")

#: The verifier is 32 random bytes in base64url, the same length.
VERIFIER_RE = CHALLENGE_RE

SESSION_KEY = "app_auth"
FLOW_LIFETIME = timedelta(minutes=15)
TICKET_LIFETIME = timedelta(seconds=120)

#: Used and expired tickets older than this are deleted on every new ticket.
TICKET_RETENTION = timedelta(minutes=10)


class AppAuthRedeemThrottle(SimpleRateThrottle):
    """Per-IP limit on redeem attempts, signed in or not.

    Rate: ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["app-auth-redeem"]``.
    """

    scope = "app-auth-redeem"

    def get_cache_key(self, request, view):
        """Key every request by client IP.

        :param request: Django request object
        :type request: :class:`django.http.HttpRequest`
        :param view: unused, DRF's signature
        :return: str
        """
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


def challenge_for(verifier):
    """Return the base64url SHA-256 of ``verifier``, without padding.

    :param verifier: the app's secret
    :type verifier: str
    :return: str
    """
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def ticket_hash(ticket):
    """Return the hex SHA-256 the ticket is stored under.

    :param ticket: the ticket handed to the app
    :type ticket: str
    :return: str
    """
    return hashlib.sha256(ticket.encode()).hexdigest()


def _safe_next(request, target):
    """Return ``target`` when it stays on this site, else the login default.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param target: the page the app asked to return to
    :type target: str
    :return: str
    """
    target = (target or "").strip()
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target

    return settings.LOGIN_REDIRECT_URL


def _message(request, kind, status):
    """Render the flow's one-message page.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param kind: which message, as `appauth/message.html` names them
    :type kind: str
    :param status: HTTP status code
    :type status: int
    :return: :class:`django.http.HttpResponse`
    """
    return render(request, "appauth/message.html", {"kind": kind}, status=status)


@require_GET
def app_auth_start(request, provider):
    """Begin a sign-in in the system browser and hand over to allauth.

    Any session this browser already has is logged out first, so only a
    sign-in made in this flow can reach the app.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param provider: allauth provider id
    :type provider: str
    :return: :class:`django.http.HttpResponse`
    """
    if provider not in PROVIDERS or (
        provider == "apple" and not settings.APPLE_SIGN_IN_ENABLED
    ):
        raise Http404

    challenge = request.GET.get("challenge", "")
    if not CHALLENGE_RE.match(challenge):
        return _message(request, "failed", 400)

    next_url = _safe_next(request, request.GET.get("next"))
    logout(request)
    request.session[SESSION_KEY] = {
        "challenge": challenge,
        "next": next_url,
        "started": timezone.now().timestamp(),
    }
    return render(
        request,
        "appauth/start.html",
        {
            "action": reverse(f"{provider}_login"),
            "complete": reverse("app_auth_complete"),
            "provider_name": PROVIDERS[provider],
        },
    )


@require_GET
def app_auth_complete(request):
    """Turn the browser's fresh sign-in into a ticket and log the browser out.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.HttpResponse`
    """
    flow = request.session.get(SESSION_KEY)
    if not request.user.is_authenticated or not isinstance(flow, dict):
        return _message(request, "failed", 400)

    now = timezone.now()
    started = datetime.fromtimestamp(flow.get("started", 0), tz=dt_timezone.utc)
    if now - started > FLOW_LIFETIME:
        return _message(request, "failed", 400)

    AppLoginTicket.objects.filter(created_at__lt=now - TICKET_RETENTION).delete()
    ticket = secrets.token_urlsafe(32)
    AppLoginTicket.objects.create(
        ticket_hash=ticket_hash(ticket),
        user=request.user,
        challenge=flow["challenge"],
        next_url=flow["next"],
        expires_at=now + TICKET_LIFETIME,
    )
    logout(request)
    # Relative on purpose: the OS matches the callback on this host
    # (iOS webcredentials, Android Auth Tab); see docs/logbook.md.
    return HttpResponseRedirect(
        reverse("app_auth_return") + "?" + urlencode({"ticket": ticket})
    )


@require_GET
def app_auth_return(request):
    """Answer the callback URL when a plain browser opens it.

    The app's sign-in sheet stops before loading this page; the ticket is
    never echoed or redeemed here.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.HttpResponse`
    """
    return _message(request, "return", 200)


def _redeemable(ticket, verifier):
    """Return the ticket's row when every check passes.

    A known ticket is spent by any attempt, so a wrong verifier burns it.

    :param ticket: the ticket from the callback
    :type ticket: str
    :param verifier: the app's secret behind the ticket's challenge
    :type verifier: str
    :return: :class:`core.models.AppLoginTicket` or None
    """
    if not ticket or not VERIFIER_RE.match(verifier):
        logger.info("App sign-in refused: malformed request")
        return None

    with transaction.atomic():
        row = (
            AppLoginTicket.objects.select_for_update()
            .select_related("user")
            .filter(ticket_hash=ticket_hash(ticket))
            .first()
        )
        if row is None:
            reason = "unknown ticket"
        elif row.used_at is not None:
            reason = "used ticket"
        elif row.expires_at <= timezone.now():
            reason = "expired ticket"
        elif not hmac.compare_digest(challenge_for(verifier), row.challenge):
            reason = "wrong verifier"
        elif not row.user.is_active:
            reason = "inactive user"
        else:
            reason = None
        if row is not None and row.used_at is None:
            row.used_at = timezone.now()
            row.save(update_fields=["used_at"])

    if reason:
        logger.info("App sign-in refused: %s", reason)
        return None

    return row


@require_POST
def app_auth_redeem(request):
    """Sign the app's WebView in with a ticket and its verifier.

    Every refusal answers the same page and status.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.HttpResponse`
    """
    if not AppAuthRedeemThrottle().allow_request(request, None):
        return _message(request, "throttled", 429)

    row = _redeemable(request.POST.get("ticket", ""), request.POST.get("verifier", ""))
    if row is None:
        return _message(request, "expired", 400)

    from allauth.account import app_settings as account_settings
    from allauth.account.utils import perform_login

    row.user.backend = "allauth.account.auth_backends.AuthenticationBackend"
    return perform_login(
        request,
        row.user,
        email_verification=account_settings.EMAIL_VERIFICATION,
        redirect_url=row.next_url,
    )
