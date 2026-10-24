"""Sign in with Apple's REST API: revoking a user's tokens (F5).

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
REVOKE_TIMEOUT = 10  # seconds


def apple_client_secret(now=None):
    """Return the ES256-signed client secret Apple's REST API expects.

    :param now: Unix time to issue it at, for tests
    :type now: int
    :return: str
    """
    issued = int(now if now is not None else time.time())
    return jwt.encode(
        {
            "iss": settings.APPLE_TEAM_ID,
            "iat": issued,
            "exp": issued + 300,
            "aud": APPLE_AUDIENCE,
            "sub": settings.APPLE_CLIENT_ID,
        },
        settings.APPLE_PRIVATE_KEY,
        algorithm="ES256",
        headers={"kid": settings.APPLE_KEY_ID},
    )


def revoke_apple_token(refresh_token):
    """Ask Apple to revoke `refresh_token`; return True if Apple accepted.

    :param refresh_token: the token Sign in with Apple issued
    :type refresh_token: str
    :return: bool
    """
    if not settings.APPLE_SIGN_IN_ENABLED:
        logger.warning("Sign in with Apple is not configured; token not revoked")
        return False

    try:
        response = requests.post(
            APPLE_REVOKE_URL,
            data={
                "client_id": settings.APPLE_CLIENT_ID,
                "client_secret": apple_client_secret(),
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

    if not revoke_apple_token(kept.refresh_token):
        return False

    kept.delete()
    return True
