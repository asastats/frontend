"""Sign in with Apple's REST API: revoking a user's tokens (F5), exchanging
the native sheet's authorization code (O3).

Apple's account deletion guidance; see docs/logbook.md.
"""

import logging
import time

import jwt
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

APPLE_AUDIENCE = "https://appleid.apple.com"
APPLE_REVOKE_URL = "https://appleid.apple.com/auth/revoke"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
REVOKE_TIMEOUT = 10  # seconds


def apple_client_secret(now=None, client_id=""):
    """Return the ES256-signed client secret Apple's REST API expects.

    :param now: Unix time to issue it at, for tests
    :type now: int
    :param client_id: the token's client; empty is the website's Services ID
    :type client_id: str
    :return: str
    """
    issued = int(now if now is not None else time.time())
    return jwt.encode(
        {
            "iss": settings.APPLE_TEAM_ID,
            "iat": issued,
            "exp": issued + 300,
            "aud": APPLE_AUDIENCE,
            "sub": client_id or settings.APPLE_CLIENT_ID,
        },
        settings.APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": settings.APPLE_KEY_ID},
    )


def revoke_apple_token(refresh_token, client_id=""):
    """Ask Apple to revoke `refresh_token`; return True if Apple accepted.

    :param refresh_token: the token Sign in with Apple issued
    :type refresh_token: str
    :param client_id: who it was issued to; empty is the website's Services ID
    :type client_id: str
    :return: bool
    """
    if not settings.APPLE_SIGN_IN_ENABLED:
        logger.warning("Sign in with Apple is not configured; token not revoked")
        return False

    try:
        response = requests.post(
            APPLE_REVOKE_URL,
            data={
                "client_id": client_id or settings.APPLE_CLIENT_ID,
                "client_secret": apple_client_secret(client_id=client_id),
                "token": refresh_token,
                "token_type_hint": "refresh_token",
            },
            timeout=REVOKE_TIMEOUT,
        )
    except requests.RequestException as error:
        logger.warning("Apple token revocation failed: %s", error)
        return False

    if response.status_code != 200:
        logger.warning("Apple refused the token revocation: %s", response.status_code)
        return False

    return True


def revoke_for_user(user):
    """Revoke and forget `user`'s Apple token, if one is kept.

    The row stays when Apple cannot be reached, for `delete_deactivated` to
    try again; it is deleted with the user either way.

    :param user: the account being closed or deleted
    :type user: :class:`django.contrib.auth.models.User`
    :return: bool, whether nothing is left to revoke
    """
    from core.models import AppleSignInToken

    kept = AppleSignInToken.objects.filter(user=user).first()
    if kept is None:
        return True

    if not revoke_apple_token(kept.refresh_token, kept.client_id):
        return False

    kept.delete()
    return True


def exchange_apple_code(code, client_id):
    """Exchange a native sheet's authorization code for Apple's tokens.

    :param code: the sheet's one-time authorization code
    :type code: str
    :param client_id: the app's bundle id the code was issued to
    :type client_id: str
    :return: dict with ``access_token`` and ``refresh_token``, or None
    """
    try:
        response = requests.post(
            APPLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": apple_client_secret(client_id=client_id),
                "code": code,
                "grant_type": "authorization_code",
            },
            timeout=REVOKE_TIMEOUT,
        )
    except requests.RequestException as error:
        logger.warning("Apple code exchange failed: %s", error)
        return None

    if response.status_code != 200:
        logger.warning("Apple refused the code exchange: %s", response.status_code)
        return None

    tokens = response.json()
    if not tokens.get("refresh_token"):
        logger.warning("Apple's code exchange returned no refresh token")
        return None

    return tokens
