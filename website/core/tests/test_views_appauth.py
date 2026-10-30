"""Testing module for :py:mod:`core.views_appauth` module."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import AppLoginTicket
from core.views_appauth import (
    FLOW_LIFETIME,
    PROVIDERS,
    SESSION_KEY,
    TICKET_LIFETIME,
    TICKET_RETENTION,
    AppAuthRedeemThrottle,
    _safe_next,
    challenge_for,
    ticket_hash,
)

VERIFIER = "v" * 43
CHALLENGE = challenge_for(VERIFIER)


@pytest.fixture(autouse=True)
def _clear_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="appuser", password="secret-pw")


def _start(client, provider="github", challenge=CHALLENGE, next_url="/home/"):
    return client.get(
        reverse("app_auth_start", args=[provider]),
        {"challenge": challenge, "next": next_url},
    )


def _ticket_from(response):
    return parse_qs(urlparse(response["Location"]).query)["ticket"][0]


def _complete(client, user, **start):
    _start(client, **start)
    client.force_login(user)
    return client.get(reverse("app_auth_complete"))


def _redeem(client, ticket, verifier=VERIFIER):
    return client.post(
        reverse("app_auth_redeem"), {"ticket": ticket, "verifier": verifier}
    )


class TestCoreViewsAppauthHelpers:
    """Testing class for the module's helpers."""

    def test_core_views_appauth_challenge_is_base64url_sha256_without_padding(self):
        # RFC 7636 appendix B's example verifier and challenge.
        assert (
            challenge_for("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk")
            == "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
        )

    def test_core_views_appauth_ticket_hash_is_hex_sha256(self):
        assert ticket_hash("abc") == (
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )

    def test_core_views_appauth_providers_match_the_buttons(self):
        assert sorted(PROVIDERS) == [
            "apple",
            "discord",
            "github",
            "google",
            "reddit",
            "twitter_oauth2",
        ]

    @pytest.mark.parametrize(
        "target,expected",
        [
            ("/profile/", "/profile/"),
            ("  /widgets/  ", "/widgets/"),
            ("https://evil.example/", "/home/"),
            ("//evil.example/", "/home/"),
            ("", "/home/"),
            (None, "/home/"),
        ],
    )
    def test_core_views_appauth_safe_next(self, rf, target, expected):
        assert _safe_next(rf.get("/"), target) == expected

    def test_core_views_appauth_throttle_keys_by_ip_even_when_signed_in(self, rf):
        request = rf.post("/", REMOTE_ADDR="10.0.0.9")

        assert AppAuthRedeemThrottle().get_cache_key(request, None) == (
            "throttle_app-auth-redeem_10.0.0.9"
        )


@pytest.mark.django_db
class TestCoreViewsAppauthStart:
    """Testing class for :py:func:`core.views_appauth.app_auth_start`."""

    def test_core_views_appauth_start_url(self):
        assert reverse("app_auth_start", args=["google"]) == "/app/auth/start/google/"

    def test_core_views_appauth_start_unknown_provider_404(self, client):
        assert _start(client, provider="facebook").status_code == 404

    @override_settings(APPLE_SIGN_IN_ENABLED=False)
    def test_core_views_appauth_start_apple_off_404(self, client):
        assert _start(client, provider="apple").status_code == 404

    @override_settings(APPLE_SIGN_IN_ENABLED=True)
    def test_core_views_appauth_start_apple_on(self, client):
        response = _start(client, provider="apple")

        assert response.status_code == 200
        assert response.context["action"] == "/accounts/apple/login/"

    @pytest.mark.parametrize("challenge", ["", "short", "x" * 44, "+" * 43, "=" * 43])
    def test_core_views_appauth_start_bad_challenge_400(self, client, challenge):
        response = _start(client, challenge=challenge)

        assert response.status_code == 400
        assert response.context["kind"] == "failed"
        assert SESSION_KEY not in client.session

    def test_core_views_appauth_start_post_405(self, client):
        response = client.post(reverse("app_auth_start", args=["github"]))

        assert response.status_code == 405

    def test_core_views_appauth_start_stores_the_flow(self, client):
        _start(client, next_url="/profile/")
        flow = client.session[SESSION_KEY]

        assert flow["challenge"] == CHALLENGE
        assert flow["next"] == "/profile/"
        assert abs(flow["started"] - timezone.now().timestamp()) < 5

    def test_core_views_appauth_start_replaces_an_unsafe_next(self, client):
        _start(client, next_url="https://evil.example/")

        assert client.session[SESSION_KEY]["next"] == "/home/"

    def test_core_views_appauth_start_logs_the_browser_out(self, client, user):
        client.force_login(user)

        _start(client)

        assert AUTH_SESSION_KEY not in client.session
        assert SESSION_KEY in client.session

    def test_core_views_appauth_start_posts_to_allauth(self, client):
        response = _start(client, provider="google")
        html = response.content.decode()

        assert response.context["action"] == "/accounts/google/login/"
        assert (
            'id="id_app_auth_start" method="POST" action="/accounts/google/login/"'
            in html
        )
        assert '<input type="hidden" name="process" value="login">' in html
        assert '<input type="hidden" name="next" value="/app/auth/complete/">' in html
        assert "csrfmiddlewaretoken" in html
        assert "Continue with Google" in html
        assert 'src="/static/js/appauth-start.js"' in html

    def test_core_views_appauth_start_released_x_id_posts_to_oauth1(self, client):
        response = _start(client, provider="twitter_oauth2")

        assert response.context["action"] == "/accounts/twitter/login/"
        assert "Continue with X" in response.content.decode()


@pytest.mark.django_db
class TestCoreViewsAppauthComplete:
    """Testing class for :py:func:`core.views_appauth.app_auth_complete`."""

    def test_core_views_appauth_complete_anonymous_400(self, client):
        _start(client)

        response = client.get(reverse("app_auth_complete"))

        assert response.status_code == 400
        assert response.context["kind"] == "failed"
        assert not AppLoginTicket.objects.exists()

    def test_core_views_appauth_complete_without_flow_400(self, client, user):
        client.force_login(user)

        response = client.get(reverse("app_auth_complete"))

        assert response.status_code == 400
        assert not AppLoginTicket.objects.exists()

    def test_core_views_appauth_complete_stale_flow_400(self, client, user):
        _start(client)
        session = client.session
        session[SESSION_KEY]["started"] -= FLOW_LIFETIME.total_seconds() + 1
        session.save()
        client.force_login(user)

        response = client.get(reverse("app_auth_complete"))

        assert response.status_code == 400
        assert not AppLoginTicket.objects.exists()

    def test_core_views_appauth_complete_keeps_only_the_hash(self, client, user):
        response = _complete(client, user, next_url="/profile/")
        ticket = _ticket_from(response)
        row = AppLoginTicket.objects.get()

        assert row.ticket_hash == ticket_hash(ticket)
        assert row.user == user
        assert row.challenge == CHALLENGE
        assert row.next_url == "/profile/"
        assert row.used_at is None
        assert row.expires_at - row.created_at == pytest.approx(
            TICKET_LIFETIME, abs=timedelta(seconds=2)
        )
        assert ticket not in str(AppLoginTicket.objects.values_list())

    def test_core_views_appauth_complete_redirects_to_the_callback(self, client, user):
        response = _complete(client, user)

        assert response.status_code == 302
        assert response["Location"].startswith("/app/auth/return/?ticket=")
        assert len(_ticket_from(response)) == 43

    def test_core_views_appauth_complete_logs_the_browser_out(self, client, user):
        _complete(client, user)

        assert AUTH_SESSION_KEY not in client.session
        assert SESSION_KEY not in client.session

    def test_core_views_appauth_complete_deletes_old_tickets(self, client, user):
        old = AppLoginTicket.objects.create(
            ticket_hash="0" * 64,
            user=user,
            challenge=CHALLENGE,
            next_url="/home/",
            expires_at=timezone.now(),
        )
        AppLoginTicket.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - TICKET_RETENTION - timedelta(seconds=1)
        )

        _complete(client, user)

        assert not AppLoginTicket.objects.filter(pk=old.pk).exists()
        assert AppLoginTicket.objects.count() == 1


@pytest.mark.django_db
class TestCoreViewsAppauthReturn:
    """Testing class for :py:func:`core.views_appauth.app_auth_return`."""

    def test_core_views_appauth_return_url_matches_the_native_callback(self):
        assert reverse("app_auth_return") == "/app/auth/return/"

    def test_core_views_appauth_return_neither_echoes_nor_redeems(self, client, user):
        ticket = _ticket_from(_complete(client, user))

        response = client.get(reverse("app_auth_return"), {"ticket": ticket})

        assert response.status_code == 200
        assert response.context["kind"] == "return"
        assert ticket not in response.content.decode()
        assert AppLoginTicket.objects.get().used_at is None


@pytest.mark.django_db
class TestCoreViewsAppauthRedeem:
    """Testing class for :py:func:`core.views_appauth.app_auth_redeem`."""

    def _ticket(self, client, user, **start):
        ticket = _ticket_from(_complete(client, user, **start))
        client.logout()
        return ticket

    def _refused(self, response):
        assert response.status_code == 400
        assert response.context["kind"] == "expired"

    def test_core_views_appauth_redeem_get_405(self, client):
        assert client.get(reverse("app_auth_redeem")).status_code == 405

    def test_core_views_appauth_redeem_needs_csrf(self, user):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        ticket = self._ticket(client, user)

        assert _redeem(client, ticket).status_code == 403

    def test_core_views_appauth_redeem_signs_in_and_goes_next(self, client, user):
        ticket = self._ticket(client, user, next_url="/profile/")

        response = _redeem(client, ticket)

        assert response.status_code == 302
        assert response["Location"] == "/profile/"
        assert int(client.session[AUTH_SESSION_KEY]) == user.pk
        assert AppLoginTicket.objects.get().used_at is not None

    def test_core_views_appauth_redeem_twice_fails(self, client, user):
        ticket = self._ticket(client, user)
        _redeem(client, ticket)
        client.logout()

        self._refused(_redeem(client, ticket))
        assert AUTH_SESSION_KEY not in client.session

    @pytest.mark.parametrize(
        "ticket,verifier",
        [("", VERIFIER), ("t", ""), ("t", "short"), ("t", "+" * 43)],
    )
    def test_core_views_appauth_redeem_malformed(self, client, ticket, verifier):
        self._refused(_redeem(client, ticket, verifier))

    def test_core_views_appauth_redeem_unknown_ticket(self, client, user):
        self._ticket(client, user)

        self._refused(_redeem(client, "not-a-ticket"))

    def test_core_views_appauth_redeem_expired(self, client, user):
        ticket = self._ticket(client, user)
        AppLoginTicket.objects.update(expires_at=timezone.now())

        self._refused(_redeem(client, ticket))
        assert AUTH_SESSION_KEY not in client.session

    def test_core_views_appauth_redeem_wrong_verifier_burns_the_ticket(
        self, client, user
    ):
        ticket = self._ticket(client, user)

        self._refused(_redeem(client, ticket, "w" * 43))
        self._refused(_redeem(client, ticket))
        assert AUTH_SESSION_KEY not in client.session

    def test_core_views_appauth_redeem_inactive_user(self, client, user):
        ticket = self._ticket(client, user)
        get_user_model().objects.filter(pk=user.pk).update(is_active=False)

        self._refused(_redeem(client, ticket))
        assert AUTH_SESSION_KEY not in client.session

    def test_core_views_appauth_redeem_logs_the_reason(self, client, user, caplog):
        ticket = self._ticket(client, user)
        caplog.set_level("INFO", logger="core.views_appauth")

        _redeem(client, ticket, "w" * 43)

        assert "App sign-in refused: wrong verifier" in caplog.text

    def test_core_views_appauth_redeem_throttled(self, client):
        for _ in range(10):
            _redeem(client, "t")

        response = _redeem(client, "t")

        assert response.status_code == 429
        assert response.context["kind"] == "throttled"
