"""Sign in with Apple (F5): provider configuration and the button."""

import pytest
from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse


class TestSignInWithAppleConfiguration:
    """The allauth provider reads its four parts from settings."""

    def test_apple_provider_is_installed(self):
        assert "allauth.socialaccount.providers.apple" in settings.INSTALLED_APPS

    def test_apple_provider_maps_allauths_names(self):
        app = settings.SOCIALACCOUNT_PROVIDERS["apple"]["APP"]

        # Services ID first (allauth's API calls), then the app's bundle id (O3).
        assert app["client_id"] == ",".join(
            filter(None, (settings.APPLE_CLIENT_ID, settings.APPLE_APP_BUNDLE_ID))
        )
        assert app["client_id"].endswith("com.asastats.app")
        assert app["secret"] == settings.APPLE_KEY_ID
        assert app["key"] == settings.APPLE_TEAM_ID
        assert app["settings"]["certificate_key"] == settings.APPLE_PRIVATE_KEY

    def test_apple_sign_in_is_off_without_keys(self):
        # The test environment sets none of the four.
        assert settings.APPLE_SIGN_IN_ENABLED is False

    def test_apple_login_and_callback_urls(self):
        assert reverse("apple_login") == "/accounts/apple/login/"
        assert reverse("apple_callback") == "/accounts/apple/login/callback/"


@pytest.mark.django_db
class TestSignInWithAppleButton:
    """The button appears only when Sign in with Apple is configured."""

    @pytest.fixture(autouse=True)
    def _capabilities(self, mocker):
        mocker.patch(
            "core.context_processors.fetch_capabilities", return_value={"permission": 0}
        )

    def _page(self, name):
        return Client().get(reverse(name)).content.decode()

    @override_settings(APPLE_SIGN_IN_ENABLED=True)
    @pytest.mark.parametrize("name", ["account_login", "account_signup", "faq"])
    def test_apple_button_when_configured(self, name):
        html = self._page(name)

        assert 'id="id_apple"' in html
        assert "Sign in with Apple" in html
        assert 'href="/accounts/apple/login/"' in html

    @pytest.mark.parametrize("name", ["account_login", "account_signup", "faq"])
    def test_no_apple_button_without_keys(self, name):
        assert "Sign in with Apple" not in self._page(name)

    def test_apple_button_comes_first_among_social_providers(self):
        with override_settings(APPLE_SIGN_IN_ENABLED=True):
            html = self._page("account_login")

        assert html.index("Sign in with Apple") < html.index("Sign in with Discord")

    def test_connections_page_hides_apple_without_keys(self, django_user_model):
        user = django_user_model.objects.create_user(username="connect", password="x")
        client = Client()
        client.force_login(user)

        html = client.get(reverse("socialaccount_connections")).content.decode()

        assert "/accounts/apple/login/" not in html
        assert "/accounts/github/login/" in html


from types import SimpleNamespace

import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from core.apple import (
    APPLE_AUDIENCE,
    APPLE_REVOKE_URL,
    APPLE_TOKEN_URL,
    apple_client_secret,
    exchange_apple_code,
    revoke_apple_token,
    revoke_for_user,
)
from core.models import AppleSignInToken
from core.signals import (
    keep_apple_token,
    keep_apple_token_on_login,
    keep_apple_token_on_signup,
    user_deactivated,
)

_KEY = ec.generate_private_key(ec.SECP256R1())
_PEM = _KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()

APPLE_CONFIGURED = override_settings(
    APPLE_CLIENT_ID="com.asastats.web",
    APPLE_KEY_ID="KEY1234567",
    APPLE_TEAM_ID="DF2V3954Z7",
    APPLE_PRIVATE_KEY=_PEM,
    APPLE_SIGN_IN_ENABLED=True,
)


def _sociallogin(user, provider="apple", secret="r.refresh", state=None):
    token = SimpleNamespace(token_secret=secret) if secret is not None else None
    return SimpleNamespace(
        user=user,
        account=SimpleNamespace(provider=provider),
        token=token,
        state=state or {},
    )


class TestAppleClientSecret:
    """The ES256 client secret for Apple's REST API."""

    @APPLE_CONFIGURED
    def test_apple_client_secret_claims_and_key_id(self):
        secret = apple_client_secret(now=1_700_000_000)

        assert jwt.get_unverified_header(secret)["kid"] == "KEY1234567"
        claims = jwt.decode(
            secret,
            _KEY.public_key(),
            algorithms=["ES256"],
            audience=APPLE_AUDIENCE,
            options={"verify_exp": False},
        )
        assert claims == {
            "iss": "DF2V3954Z7",
            "iat": 1_700_000_000,
            "exp": 1_700_000_300,
            "aud": APPLE_AUDIENCE,
            "sub": "com.asastats.web",
        }

    @APPLE_CONFIGURED
    def test_apple_client_secret_defaults_to_now(self, mocker):
        mocker.patch("core.apple.time.time", return_value=1_800_000_000.5)

        claims = jwt.decode(
            apple_client_secret(),
            _KEY.public_key(),
            algorithms=["ES256"],
            audience=APPLE_AUDIENCE,
            options={"verify_exp": False, "verify_iat": False},
        )
        assert claims["iat"] == 1_800_000_000


class TestRevokeAppleToken:
    """Testing class for :py:func:`core.apple.revoke_apple_token`."""

    def test_revoke_apple_token_does_nothing_unconfigured(self, mocker):
        post = mocker.patch("core.apple.requests.post")

        assert revoke_apple_token("r.refresh") is False
        post.assert_not_called()

    @APPLE_CONFIGURED
    def test_revoke_apple_token_posts_to_apple(self, mocker):
        post = mocker.patch(
            "core.apple.requests.post", return_value=mocker.Mock(status_code=200)
        )

        assert revoke_apple_token("r.refresh") is True
        url = post.call_args.args[0]
        data = post.call_args.kwargs["data"]
        assert url == APPLE_REVOKE_URL
        assert data["client_id"] == "com.asastats.web"
        assert data["token"] == "r.refresh"
        assert data["token_type_hint"] == "refresh_token"
        assert jwt.get_unverified_header(data["client_secret"])["alg"] == "ES256"
        assert post.call_args.kwargs["timeout"] == 10

    @APPLE_CONFIGURED
    def test_revoke_apple_token_refused(self, mocker):
        mocker.patch("core.apple.requests.post", return_value=mocker.Mock(status_code=400))

        assert revoke_apple_token("r.refresh") is False

    @APPLE_CONFIGURED
    def test_revoke_apple_token_unreachable(self, mocker):
        mocker.patch(
            "core.apple.requests.post", side_effect=requests.ConnectionError("down")
        )

        assert revoke_apple_token("r.refresh") is False


@pytest.mark.django_db
class TestAppleTokenLifecycle:
    """Kept at Apple sign-in, revoked and forgotten when the account closes."""

    def _user(self, django_user_model, name="appleuser"):
        return django_user_model.objects.create_user(username=name, password="x")

    def test_keep_apple_token_stores_and_updates(self, django_user_model):
        user = self._user(django_user_model)

        keep_apple_token(_sociallogin(user, secret="r.first"))
        keep_apple_token(_sociallogin(user, secret="r.second"))

        assert AppleSignInToken.objects.get(user=user).refresh_token == "r.second"

    @pytest.mark.parametrize(
        "provider,secret", [("github", "r.x"), ("apple", ""), ("apple", None)]
    )
    def test_keep_apple_token_ignores_others(self, django_user_model, provider, secret):
        user = self._user(django_user_model)

        keep_apple_token(_sociallogin(user, provider=provider, secret=secret))

        assert not AppleSignInToken.objects.filter(user=user).exists()

    def test_keep_apple_token_on_login_receiver(self, django_user_model):
        user = self._user(django_user_model)

        keep_apple_token_on_login(None, None, _sociallogin(user))

        assert AppleSignInToken.objects.filter(user=user).exists()

    def test_keep_apple_token_on_signup_receiver(self, django_user_model):
        user = self._user(django_user_model)

        keep_apple_token_on_signup(None, None, user)
        assert not AppleSignInToken.objects.filter(user=user).exists()

        keep_apple_token_on_signup(None, None, user, sociallogin=_sociallogin(user))
        assert AppleSignInToken.objects.filter(user=user).exists()

    def test_revoke_for_user_without_a_token(self, django_user_model, mocker):
        revoke = mocker.patch("core.apple.revoke_apple_token")

        assert revoke_for_user(self._user(django_user_model)) is True
        revoke.assert_not_called()

    def test_revoke_for_user_forgets_a_revoked_token(self, django_user_model, mocker):
        user = self._user(django_user_model)
        AppleSignInToken.objects.create(user=user, refresh_token="r.refresh")
        mocker.patch("core.apple.revoke_apple_token", return_value=True)

        assert revoke_for_user(user) is True
        assert not AppleSignInToken.objects.filter(user=user).exists()

    def test_revoke_for_user_keeps_it_for_a_retry(self, django_user_model, mocker):
        user = self._user(django_user_model)
        AppleSignInToken.objects.create(user=user, refresh_token="r.refresh")
        mocker.patch("core.apple.revoke_apple_token", return_value=False)

        assert revoke_for_user(user) is False
        assert AppleSignInToken.objects.filter(user=user).exists()

    @APPLE_CONFIGURED
    def test_closing_the_account_revokes_at_apple(self, django_user_model, mocker):
        user = self._user(django_user_model)
        AppleSignInToken.objects.create(user=user, refresh_token="r.refresh")
        post = mocker.patch(
            "core.apple.requests.post", return_value=mocker.Mock(status_code=200)
        )

        user_deactivated.send(sender=django_user_model, user=user)

        assert post.call_args.kwargs["data"]["token"] == "r.refresh"
        assert not AppleSignInToken.objects.filter(user=user).exists()

    def test_deletion_tries_again_and_deletes_the_token(self, django_user_model, mocker):
        from utils.userhelpers import delete_deactivated

        user = django_user_model.objects.create(username="closedapple", is_active=False)
        AppleSignInToken.objects.create(user=user, refresh_token="r.refresh")
        revoke = mocker.patch("core.apple.revoke_apple_token", return_value=False)

        assert delete_deactivated() == 1

        revoke.assert_called_once_with("r.refresh", "")
        assert not AppleSignInToken.objects.exists()

    def test_keep_apple_token_stores_the_native_client(self, django_user_model):
        user = self._user(django_user_model)

        keep_apple_token(
            _sociallogin(user, state={"apple_client_id": "com.asastats.app"})
        )

        assert AppleSignInToken.objects.get(user=user).client_id == "com.asastats.app"

    def test_revoke_for_user_uses_the_issued_client(self, django_user_model, mocker):
        user = self._user(django_user_model)
        AppleSignInToken.objects.create(
            user=user, refresh_token="r.app", client_id="com.asastats.app"
        )
        revoke = mocker.patch("core.apple.revoke_apple_token", return_value=True)

        revoke_for_user(user)

        revoke.assert_called_once_with("r.app", "com.asastats.app")


class TestAppleNativeClient:
    """Native sign-in (O3): the app's bundle id as Apple's client."""

    @APPLE_CONFIGURED
    def test_apple_client_secret_for_the_app(self):
        secret = apple_client_secret(now=1_700_000_000, client_id="com.asastats.app")
        claims = jwt.decode(secret, options={"verify_signature": False})
        assert claims["sub"] == "com.asastats.app"

    @APPLE_CONFIGURED
    def test_revoke_apple_token_for_the_app(self, mocker):
        post = mocker.patch(
            "core.apple.requests.post", return_value=mocker.Mock(status_code=200)
        )

        assert revoke_apple_token("r.app", "com.asastats.app") is True
        assert post.call_args.kwargs["data"]["client_id"] == "com.asastats.app"

    @APPLE_CONFIGURED
    def test_exchange_apple_code(self, mocker):
        response = mocker.Mock(status_code=200)
        response.json.return_value = {"access_token": "a", "refresh_token": "r"}
        post = mocker.patch("core.apple.requests.post", return_value=response)

        assert exchange_apple_code("c.code", "com.asastats.app") == {
            "access_token": "a",
            "refresh_token": "r",
        }
        assert post.call_args.args[0] == APPLE_TOKEN_URL
        data = post.call_args.kwargs["data"]
        assert data["grant_type"] == "authorization_code"
        assert data["client_id"] == "com.asastats.app"

    @APPLE_CONFIGURED
    def test_exchange_apple_code_without_refresh_token(self, mocker):
        response = mocker.Mock(status_code=200)
        response.json.return_value = {"access_token": "a"}
        mocker.patch("core.apple.requests.post", return_value=response)

        assert exchange_apple_code("c.code", "com.asastats.app") is None

    @APPLE_CONFIGURED
    def test_exchange_apple_code_refused(self, mocker):
        mocker.patch(
            "core.apple.requests.post", return_value=mocker.Mock(status_code=400)
        )

        assert exchange_apple_code("c.code", "com.asastats.app") is None

    @APPLE_CONFIGURED
    def test_exchange_apple_code_unreachable(self, mocker):
        mocker.patch(
            "core.apple.requests.post", side_effect=requests.ConnectionError("down")
        )

        assert exchange_apple_code("c.code", "com.asastats.app") is None
