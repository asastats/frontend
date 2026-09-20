"""Testing module for :py:mod:`api.authentication`.

A revocation that does not revoke is worse than none, because it would be
trusted. So each test below states which direction it closes, and the pair
"revoked is refused" / "re-issued is accepted" is the one that matters: a
mechanism that refused everything would pass the first alone.
"""

from datetime import datetime, timedelta, timezone

import pytest
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

from api.authentication import RevocableJWTAuthentication


class _Profile:
    """The one attribute the authentication class reads."""

    def __init__(self, cutoff=None):
        self.api_tokens_valid_from = cutoff


class _User:
    """A user with - or without - a profile."""

    pk = 7

    def __init__(self, profile=None):
        if profile is not None:
            self.profile = profile


def _token(issued_at=None):
    """Return a token carrying `issued_at` as its `iat`."""
    token = AccessToken()
    token["user_id"] = _User.pk
    if issued_at is not None:
        token.payload["iat"] = int(issued_at.timestamp())
    return token


@pytest.fixture
def auth(mocker):
    """Return the class with simplejwt's own user lookup stubbed out.

    `super().get_user` is the library's business - user exists, user is active
    - and is covered by its own suite. What is under test is the layer added
    on top of it.
    """
    instance = RevocableJWTAuthentication()
    mocker.patch(
        "api.authentication.JWTAuthentication.get_user",
        side_effect=lambda token: instance._user,
    )
    return instance


class TestRevocableJWTAuthentication:
    """Revocation by `iat`, in both directions."""

    def test_api_authentication_accepts_a_token_when_nothing_is_revoked(self, auth):
        """The overwhelmingly common case must cost nothing and change nothing."""
        auth._user = _User(_Profile(cutoff=None))

        assert auth.get_user(_token(datetime.now(timezone.utc))) is auth._user

    def test_api_authentication_refuses_a_token_issued_before_the_cutoff(self, auth):
        """**The point of the mechanism.**

        A leaked credential stays signature-valid until it expires, and the
        only other kill switch - rotating `SIMPLE_JWT_KEY` - would take
        `WIDGETS_API_TOKEN` and the published mobile app's token with it.
        """
        now = datetime.now(timezone.utc)
        auth._user = _User(_Profile(cutoff=now))

        with pytest.raises(AuthenticationFailed) as raised:
            auth.get_user(_token(now - timedelta(seconds=1)))

        # simplejwt renders `detail` and `code` as a dict, which is also the
        # body an integration receives - so this pins the wire shape, not just
        # that something was raised.
        assert raised.value.detail["code"] == "token_revoked"
        assert "revoked" in str(raised.value.detail["detail"])

    def test_api_authentication_accepts_a_token_issued_after_the_cutoff(self, auth):
        """**The other direction, and the one that makes this recoverable.**

        Re-issuing from the profile API page produces an `iat` after the
        cutoff, so the account holder fixes their own integration without us.
        Without this test, refusing everything would look like success.
        """
        now = datetime.now(timezone.utc)
        auth._user = _User(_Profile(cutoff=now))

        assert auth.get_user(_token(now + timedelta(seconds=1))) is auth._user

    def test_api_authentication_refuses_a_token_with_no_issued_at(self, auth):
        """Fails closed, because the alternative is a way around revocation.

        Every token simplejwt mints carries `iat`, so this is unreachable in
        practice - which is exactly why the direction it fails in should be
        pinned rather than left to whoever edits this next.
        """
        now = datetime.now(timezone.utc)
        auth._user = _User(_Profile(cutoff=now))
        token = _token()
        token.payload.pop("iat", None)

        with pytest.raises(AuthenticationFailed):
            auth.get_user(token)

    def test_api_authentication_survives_a_user_with_no_profile(self, auth):
        """A broken account must not turn into a 500 in the auth layer.

        `CanAccessApiPermission` already refuses a profile-less user on its own
        terms; this layer only has to not raise first.
        """
        auth._user = _User(profile=None)

        assert auth.get_user(_token(datetime.now(timezone.utc))) is auth._user
