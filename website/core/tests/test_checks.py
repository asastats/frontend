"""The WIDGETS_API_TOKEN system check has to fire on the real failure modes.

A check that only ever returns [] is worse than no check: it looks like
coverage. Both ways this token has actually broken are exercised here against
tokens built for the purpose -- an expired one, and one signed with a
different key, which is the case that reads like expiry and is not.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from core.checks import EXPIRY_WARNING_DAYS, check_widgets_api_token

#: Stand-in keys. Neither is any project's real key; the point of the pair is
#: that a token minted with one must not validate against the other.
OUR_KEY = "our-signing-key-for-tests-only-0123456789"
THEIR_KEY = "a-different-signing-key-eg-the-engines-987"


def _token(key, lifetime=timedelta(days=365)):
    """Return an HS256 access token signed with `key`.

    The claim set matches what simplejwt issues, because ``AccessToken``
    validates ``token_type`` and ``jti`` as well as the signature -- a token
    missing either would be rejected for the wrong reason and the test would
    pass while proving nothing.

    :param key: HMAC signing key
    :type key: str
    :param lifetime: how far from now the token expires
    :type lifetime: :class:`datetime.timedelta`
    :return: str
    """
    now = datetime.now(tz=timezone.utc)
    return jwt.encode(
        {
            "token_type": "access",
            "exp": int((now + lifetime).timestamp()),
            "iat": int(now.timestamp()),
            "jti": uuid.uuid4().hex,
            "user_id": 1,
        },
        key,
        algorithm="HS256",
    )


def _ids(messages):
    return [message.id for message in messages]


@pytest.fixture(autouse=True)
def our_signing_key(settings):
    """Pin the project's key for every test in this module.

    simplejwt caches its own view of SIMPLE_JWT, so both the bare
    SIMPLE_JWT_KEY the check reads and the SIGNING_KEY simplejwt validates
    with have to move together. pytest-django's `settings` fixture fires
    `setting_changed`, which is what makes simplejwt pick the new one up.
    """
    settings.SIMPLE_JWT_KEY = OUR_KEY
    settings.SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(days=365),
        "SIGNING_KEY": OUR_KEY,
    }
    return settings


class TestWidgetsApiTokenCheck:
    """Testing class for the WIDGETS_API_TOKEN system check."""

    def test_core_check_passes_for_a_healthy_token(self, our_signing_key):
        """Guard the guard: the good case must be silent."""
        our_signing_key.WIDGETS_API_TOKEN = _token(OUR_KEY)
        assert check_widgets_api_token(None) == []

    def test_core_check_reports_a_missing_signing_key(self, our_signing_key):
        our_signing_key.SIMPLE_JWT_KEY = ""
        our_signing_key.WIDGETS_API_TOKEN = "anything"
        assert _ids(check_widgets_api_token(None)) == ["asastats.E001"]

    def test_core_check_warns_when_no_token_is_configured(self, our_signing_key):
        """Absent is a warning, not an error: a checkout may not need one."""
        our_signing_key.WIDGETS_API_TOKEN = ""
        messages = check_widgets_api_token(None)
        assert _ids(messages) == ["asastats.W001"]
        assert "401" in messages[0].msg

    def test_core_check_errors_on_a_token_signed_with_another_key(
        self, our_signing_key
    ):
        """The failure that reads like expiry and is not.

        A token minted against the engine's SIMPLE_JWT_KEY carries a valid
        shape and an unexpired `exp`, so nothing about it looks wrong until
        the signature is checked.
        """
        our_signing_key.WIDGETS_API_TOKEN = _token(THEIR_KEY)
        messages = check_widgets_api_token(None)
        assert _ids(messages) == ["asastats.E002"]
        assert "mint-widgets-token.sh" in messages[0].hint
        # The two TokenError causes share an exception type and need opposite
        # advice, so the hint has to name the right one.
        assert "minted somewhere other than this project" in messages[0].hint
        assert "lapsed" not in messages[0].hint

    def test_core_check_errors_on_an_expired_token(self, our_signing_key):
        our_signing_key.WIDGETS_API_TOKEN = _token(
            OUR_KEY, lifetime=timedelta(days=-1)
        )
        messages = check_widgets_api_token(None)
        assert _ids(messages) == ["asastats.E002"]
        # ... and not the signature advice, which would send the reader after
        # the wrong problem entirely.
        assert "lapsed" in messages[0].hint
        assert "minted somewhere other than this project" not in messages[0].hint

    @pytest.mark.parametrize("days", [1, EXPIRY_WARNING_DAYS])
    def test_core_check_warns_before_a_token_lapses(self, days, our_signing_key):
        """`days` from expiry must warn while the token still works.

        :param days: remaining lifetime to test
        :type days: int
        """
        our_signing_key.WIDGETS_API_TOKEN = _token(
            OUR_KEY, lifetime=timedelta(days=days, hours=1)
        )
        messages = check_widgets_api_token(None)
        assert _ids(messages) == ["asastats.W002"]
        assert "mint-widgets-token.sh" in messages[0].hint

    def test_core_check_is_silent_well_before_expiry(self, our_signing_key):
        """One day the other side of the threshold must say nothing."""
        our_signing_key.WIDGETS_API_TOKEN = _token(
            OUR_KEY, lifetime=timedelta(days=EXPIRY_WARNING_DAYS + 2)
        )
        assert check_widgets_api_token(None) == []
