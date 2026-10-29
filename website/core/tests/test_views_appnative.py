"""Testing module for :py:mod:`core.views_appnative` module."""

import copy
import time
from datetime import timedelta

import jwt
import pytest
import requests
from allauth.socialaccount.models import SocialAccount
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from django.conf import settings
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import AppleSignInToken
from core.views_appnative import (
    GOOGLE_ISSUERS,
    NATIVE_PROVIDERS,
    NONCE_LIFETIME,
    NONCE_SESSION_KEY,
    AppAuthNativeThrottle,
    google_audiences,
    nonce_hash,
)

APP_UA = "Mozilla/5.0 (Linux; Android 14) ASAStatsApp/1.1.0 (android)"
WEB_CLIENT = "web-client.apps.googleusercontent.com"
IOS_CLIENT = "ios-client.apps.googleusercontent.com"
BUNDLE_ID = "com.asastats.app"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_APPLE_PEM = (
    ec.generate_private_key(ec.SECP256R1())
    .private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    .decode()
)


def _providers():
    providers = copy.deepcopy(settings.SOCIALACCOUNT_PROVIDERS)
    providers["google"]["APP"]["client_id"] = WEB_CLIENT
    providers["apple"]["APP"]["client_id"] = f"com.asastats.web,{BUNDLE_ID}"
    return providers


CONFIGURED = override_settings(
    SOCIALACCOUNT_PROVIDERS=_providers(),
    GOOGLE_IOS_CLIENT_ID=IOS_CLIENT,
    APPLE_SIGN_IN_ENABLED=True,
)


@pytest.fixture
def configured(settings):
    settings.SOCIALACCOUNT_PROVIDERS = _providers()
    settings.GOOGLE_IOS_CLIENT_ID = IOS_CLIENT
    settings.APPLE_SIGN_IN_ENABLED = True
    settings.APPLE_CLIENT_ID = "com.asastats.web"
    settings.APPLE_KEY_ID = "KEY1234567"
    settings.APPLE_TEAM_ID = "DF2V3954Z7"
    settings.APPLE_PRIVATE_KEY = _APPLE_PEM


@pytest.fixture(autouse=True)
def _clear_throttle():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _keys(mocker):
    """allauth fetches the providers' keys over the network: serve ours."""
    return mocker.patch(
        "allauth.socialaccount.internal.jwtkit.fetch_key",
        return_value=("RS256", _KEY.public_key()),
    )


def _token(provider="google", key=_KEY, **claims):
    now = int(time.time())
    payload = {
        "iss": "https://accounts.google.com" if provider == "google" else "https://appleid.apple.com",
        "aud": WEB_CLIENT if provider == "google" else BUNDLE_ID,
        "sub": "uid-123",
        "iat": now,
        "exp": now + 600,
        "email": "native@example.com",
        "email_verified": True,
    }
    payload.update(claims)
    return jwt.encode(payload, key, algorithm="RS256", headers={"kid": "k1"})


def _nonce(client, user_agent=APP_UA):
    response = client.post(reverse("app_native_nonce"), HTTP_USER_AGENT=user_agent)
    return response.json()["nonce"]


def _claim_for(provider, nonce):
    return nonce_hash(nonce) if provider == "apple" else nonce


def _signin(client, provider="google", nonce=None, token=None, **data):
    if nonce is None:
        nonce = _nonce(client)
    if token is None:
        token = _token(provider, nonce=_claim_for(provider, nonce))
    payload = {"provider": provider, "id_token": token, **data}
    return client.post(reverse("app_native_signin"), payload, HTTP_USER_AGENT=APP_UA)


def _apple_exchange(mocker, status=200, body=None):
    response = mocker.Mock(status_code=status)
    response.json.return_value = (
        {"access_token": "a.token", "refresh_token": "r.native"} if body is None else body
    )
    return mocker.patch("core.apple.requests.post", return_value=response)


class TestCoreViewsAppnativeHelpers:
    """Testing class for the module's helpers."""

    def test_core_views_appnative_providers(self):
        assert NATIVE_PROVIDERS == ("apple", "google")

    def test_core_views_appnative_nonce_hash_is_hex_sha256(self):
        assert nonce_hash("abc") == (
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )

    def test_core_views_appnative_google_issuers(self):
        assert GOOGLE_ISSUERS == ["https://accounts.google.com", "accounts.google.com"]

    @CONFIGURED
    def test_core_views_appnative_google_audiences_web_and_ios(self):
        assert google_audiences() == [WEB_CLIENT, IOS_CLIENT]

    @override_settings(GOOGLE_IOS_CLIENT_ID="")
    def test_core_views_appnative_google_audiences_without_ios(self):
        with override_settings(SOCIALACCOUNT_PROVIDERS=_providers()):
            assert google_audiences() == [WEB_CLIENT]

    def test_core_views_appnative_throttle_scope(self):
        assert AppAuthNativeThrottle.scope == "app-auth-native"
        assert "app-auth-native" in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]


@pytest.mark.django_db
class TestCoreViewsAppnativeNonce:
    """Testing class for :py:func:`core.views_appnative.app_native_nonce`."""

    def test_core_views_appnative_nonce_url(self):
        assert reverse("app_native_nonce") == "/app/auth/native/nonce/"

    def test_core_views_appnative_nonce_browser_404(self, client):
        assert client.post(reverse("app_native_nonce")).status_code == 404

    def test_core_views_appnative_nonce_get_405(self, client):
        response = client.get(reverse("app_native_nonce"), HTTP_USER_AGENT=APP_UA)
        assert response.status_code == 405

    @pytest.mark.usefixtures("configured")
    def test_core_views_appnative_nonce_keeps_only_the_hash(self, client):
        response = client.post(reverse("app_native_nonce"), HTTP_USER_AGENT=APP_UA)

        body = response.json()
        assert response["Cache-Control"] == "no-store"
        assert len(body["nonce"]) == 43
        assert body["google_client_id"] == WEB_CLIENT
        kept = client.session[NONCE_SESSION_KEY]
        assert kept["hash"] == nonce_hash(body["nonce"])
        assert body["nonce"] not in str(dict(client.session))

    def test_core_views_appnative_nonce_throttled(self, client, mocker):
        mocker.patch.object(AppAuthNativeThrottle, "allow_request", return_value=False)

        response = client.post(reverse("app_native_nonce"), HTTP_USER_AGENT=APP_UA)

        assert response.status_code == 429


@pytest.mark.django_db
@pytest.mark.usefixtures("configured")
class TestCoreViewsAppnativeSigninRefusals:
    """Every refusal answers the same page and status."""

    def _refused(self, response):
        assert response.status_code == 400
        assert b'data-kind="failed"' in response.content
        assert AUTH_SESSION_KEY not in response.wsgi_request.session

    def test_core_views_appnative_signin_url(self):
        assert reverse("app_native_signin") == "/app/auth/native/"

    def test_core_views_appnative_signin_browser_404(self, client):
        assert client.post(reverse("app_native_signin")).status_code == 404

    def test_core_views_appnative_signin_throttled(self, client, mocker):
        mocker.patch.object(AppAuthNativeThrottle, "allow_request", return_value=False)

        response = client.post(reverse("app_native_signin"), HTTP_USER_AGENT=APP_UA)

        assert response.status_code == 429

    def test_core_views_appnative_signin_unknown_provider(self, client):
        self._refused(_signin(client, provider="github"))

    def test_core_views_appnative_signin_apple_off(self, client):
        with override_settings(APPLE_SIGN_IN_ENABLED=False):
            self._refused(_signin(client, provider="apple"))

    def test_core_views_appnative_signin_unknown_process(self, client):
        self._refused(_signin(client, process="steal"))

    def test_core_views_appnative_signin_connect_needs_a_session(self, client):
        self._refused(_signin(client, process="connect"))

    def test_core_views_appnative_signin_without_nonce(self, client):
        token = _token(nonce="never-issued")
        self._refused(_signin(client, nonce="never-issued", token=token))

    def test_core_views_appnative_signin_stale_nonce(self, client):
        nonce = _nonce(client)
        session = client.session
        session[NONCE_SESSION_KEY]["issued"] -= NONCE_LIFETIME.total_seconds() + 1
        session.save()

        self._refused(_signin(client, nonce=nonce))

    def test_core_views_appnative_signin_nonce_is_single_use(self, client):
        nonce = _nonce(client)
        _signin(client, nonce=nonce, process="steal")

        self._refused(_signin(client, nonce=nonce))

    def test_core_views_appnative_signin_nonce_from_another_session(self, client):
        from django.test import Client

        nonce = _nonce(Client())
        _nonce(client)

        self._refused(_signin(client, nonce=nonce))

    def test_core_views_appnative_signin_token_without_nonce(self, client):
        _nonce(client)
        self._refused(_signin(client, nonce="x", token=_token()))

    def test_core_views_appnative_signin_apple_nonce_must_be_hashed(self, client):
        nonce = _nonce(client)
        token = _token("apple", nonce=nonce)
        self._refused(_signin(client, provider="apple", nonce=nonce, token=token))

    @pytest.mark.parametrize(
        "claims",
        [
            {"aud": "someone-else.apps.googleusercontent.com"},
            {"iss": "https://evil.example.com"},
            {"exp": int(time.time()) - 60},
        ],
    )
    def test_core_views_appnative_signin_bad_claims(self, client, claims):
        nonce = _nonce(client)
        self._refused(_signin(client, nonce=nonce, token=_token(nonce=nonce, **claims)))

    def test_core_views_appnative_signin_bad_signature(self, client):
        nonce = _nonce(client)
        token = _token(key=_OTHER_KEY, nonce=nonce)
        self._refused(_signin(client, nonce=nonce, token=token))

    def test_core_views_appnative_signin_missing_token(self, client):
        nonce = _nonce(client)
        self._refused(_signin(client, nonce=nonce, token=""))

    def test_core_views_appnative_signin_keys_unreachable(self, client, _keys):
        _keys.side_effect = requests.ConnectionError("down")
        self._refused(_signin(client))

    def test_core_views_appnative_signin_apple_without_code(self, client, mocker):
        post = _apple_exchange(mocker)
        self._refused(_signin(client, provider="apple"))
        post.assert_not_called()

    def test_core_views_appnative_signin_apple_exchange_refused(self, client, mocker):
        _apple_exchange(mocker, status=400)
        self._refused(_signin(client, provider="apple", code="c.code"))
        assert not AppleSignInToken.objects.exists()


@pytest.mark.django_db
@pytest.mark.usefixtures("configured")
class TestCoreViewsAppnativeSignin:
    """A verified token signs this session in, as allauth's web flow would."""

    def test_core_views_appnative_signin_google_new_user(self, client):
        response = _signin(client, next="/home/")

        account = SocialAccount.objects.get(provider="google", uid="uid-123")
        assert response.status_code == 302
        assert response["Location"] == "/home/"
        assert client.session[AUTH_SESSION_KEY] == str(account.user.pk)

    def test_core_views_appnative_signin_google_ios_audience(self, client):
        nonce = _nonce(client)
        token = _token(nonce=nonce, aud=IOS_CLIENT, iss="accounts.google.com")

        response = _signin(client, nonce=nonce, token=token)

        assert response.status_code == 302
        assert SocialAccount.objects.filter(provider="google").exists()

    def test_core_views_appnative_signin_existing_account(self, client):
        user = get_user_model().objects.create_user(username="known", password="x")
        SocialAccount.objects.create(user=user, provider="google", uid="uid-123")

        response = _signin(client, next="https://evil.example.com/")

        assert response["Location"] == settings.LOGIN_REDIRECT_URL
        assert client.session[AUTH_SESSION_KEY] == str(user.pk)

    def test_core_views_appnative_signin_apple_keeps_the_app_token(self, client, mocker):
        post = _apple_exchange(mocker)

        response = _signin(
            client, provider="apple", code="c.code", first_name="Ana", last_name="B"
        )

        assert response.status_code == 302
        kept = AppleSignInToken.objects.get()
        assert (kept.refresh_token, kept.client_id) == ("r.native", BUNDLE_ID)
        data = post.call_args.kwargs["data"]
        assert (data["client_id"], data["code"]) == (BUNDLE_ID, "c.code")
        assert jwt.decode(data["client_secret"], options={"verify_signature": False})[
            "sub"
        ] == BUNDLE_ID
        account = SocialAccount.objects.get(provider="apple")
        assert account.extra_data["name"] == {"firstName": "Ana", "lastName": "B"}

    def test_core_views_appnative_signin_connect(self, client):
        user = get_user_model().objects.create_user(username="linker", password="x")
        client.force_login(user)

        response = _signin(client, process="connect")

        assert response.status_code == 302
        assert response["Location"] == reverse("socialaccount_connections")
        assert SocialAccount.objects.get(provider="google").user == user

    def test_core_views_appnative_signin_connect_taken_account(self, client):
        owner = get_user_model().objects.create_user(username="owner", password="x")
        SocialAccount.objects.create(user=owner, provider="google", uid="uid-123")
        user = get_user_model().objects.create_user(username="other", password="x")
        client.force_login(user)

        _signin(client, process="connect")

        assert SocialAccount.objects.get(provider="google").user == owner


def test_core_views_appnative_nonce_lifetime():
    assert NONCE_LIFETIME == timedelta(minutes=5)
    assert timezone.now()
