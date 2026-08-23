"""The WIDGETS_API_TOKEN system check has to fire on the real failure modes.

A check that only ever returns [] is worse than no check: it looks like
coverage. Both ways this token has actually broken are exercised here against
tokens built for the purpose -- an expired one, and one signed with a
different key, which is the case that reads like expiry and is not.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken

from core.checks import (
    EXPIRY_WARNING_DAYS,
    ID_PREFIX,
    _expiry,
    check_export_tier_limits,
    check_widgets_api_token,
)

#: Any key that is not this project's. Stands in for the engine's, which is
#: how the real failure arrived.
THEIR_KEY = "a-different-signing-key-eg-the-engines-987"


def _our_key():
    """Return the key simplejwt will actually validate against.

    Deliberately read at call time rather than overridden. simplejwt builds
    its token backend from SIMPLE_JWT once, at import, and does not rebuild it
    when the setting changes -- so a test that overrode SIMPLE_JWT only worked
    when it happened to be the first thing in the process to import
    simplejwt. Alone it passed; in the full suite something imported first and
    the override was ignored, reporting a correctly-signed token as invalid.

    Signing with the project's own key removes the ordering dependency
    entirely, and is closer to what is being tested anyway: the check has to
    agree with whatever key this deployment really uses.
    """
    return settings.SIMPLE_JWT_KEY


def _token(key=None, lifetime=timedelta(days=365)):
    """Return an HS256 access token signed with `key`.

    The claim set matches what simplejwt issues, because ``AccessToken``
    validates ``token_type`` and ``jti`` as well as the signature -- a token
    missing either would be rejected for the wrong reason and the test would
    pass while proving nothing.

    :param key: HMAC signing key; defaults to this project's
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
        key or _our_key(),
        algorithm="HS256",
    )


def _ids(messages):
    return [message.id for message in messages]


@pytest.fixture(autouse=True)
def our_signing_key(settings):
    """Expose the settings fixture, without touching SIMPLE_JWT.

    Only WIDGETS_API_TOKEN is varied per test. SIMPLE_JWT is left exactly as
    the deployment configures it -- see _our_key for why overriding it is a
    trap.
    """
    return settings


class TestWidgetsApiTokenCheck:
    """Testing class for the WIDGETS_API_TOKEN system check."""

    def test_core_check_passes_for_a_healthy_token(self, our_signing_key):
        """Guard the guard: the good case must be silent."""
        our_signing_key.WIDGETS_API_TOKEN = _token()
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
            lifetime=timedelta(days=-1)
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
            lifetime=timedelta(days=days, hours=1)
        )
        messages = check_widgets_api_token(None)
        assert _ids(messages) == ["asastats.W002"]
        assert "mint-widgets-token.sh" in messages[0].hint

    def test_core_check_is_silent_well_before_expiry(self, our_signing_key):
        """One day the other side of the threshold must say nothing."""
        our_signing_key.WIDGETS_API_TOKEN = _token(
            lifetime=timedelta(days=EXPIRY_WARNING_DAYS + 2)
        )
        assert check_widgets_api_token(None) == []

    def test_core_check_reads_the_expiry_off_a_token(self, our_signing_key):
        """`_expiry` is where the warning threshold gets its date."""
        token = AccessToken(_token(lifetime=timedelta(days=10)))

        expires = _expiry(token)

        assert expires is not None
        assert 8 < (expires - datetime.now(tz=timezone.utc)).days < 11

    def test_core_check_survives_a_token_carrying_no_expiry(self, our_signing_key):
        """Defensive, and deliberately so.

        simplejwt validates `exp` when it builds an AccessToken, so a token
        without one cannot reach here today -- that is a guarantee of the
        library, not of this code. If it ever stops holding, the check should
        decline to judge rather than raise on every `manage.py` command.
        """

        class NoExpiry:
            payload = {"token_type": "access"}

        assert _expiry(NoExpiry()) is None

    def test_core_check_is_silent_when_the_expiry_cannot_be_read(
        self, our_signing_key, mocker
    ):
        """A token that verifies but has no readable expiry is not an error.

        It is usable right now, which is what the check is asked about; the
        warning is about a date, and there is no date to warn on.
        """
        our_signing_key.WIDGETS_API_TOKEN = _token()
        mocker.patch("core.checks._expiry", return_value=None)

        assert check_widgets_api_token(None) == []


class TestExportTierLimitsCheck:
    """Testing class for the EXPORT_TIERS_ADDRESSES_LIMIT system check.

    The setting is read from `os.environ` at import, and `load_dotenv()` finds
    `website/.env` by searching upward from the *working directory* -- so a
    server started from elsewhere silently gets the built-in defaults, which
    allow nobody below Cluster to export a single address. The symptom is one of
    two adjacent links missing from the address page, which reads like a bug in
    that link.
    """

    def test_core_check_passes_when_limits_are_configured(self, settings):
        """Guard the guard: the good case must be silent."""
        settings.EXPORT_TIERS_ADDRESSES_LIMIT = {
            "free": 5, "Intro": 6, "Asastatser": 7, "Professional": 8, "Cluster": 10
        }
        assert check_export_tier_limits(None) == []

    def test_core_check_warns_when_the_variable_is_unset(self, settings):
        """Empty means the defaults, and the defaults hide the export link."""
        settings.EXPORT_TIERS_ADDRESSES_LIMIT = {}
        messages = check_export_tier_limits(None)

        assert _ids(messages) == ["asastats.W003"]
        assert "Cluster" in messages[0].msg

    def test_core_check_names_the_tiers_that_cannot_export(self, settings):
        """The message has to say who is affected, or it is just noise."""
        settings.EXPORT_TIERS_ADDRESSES_LIMIT = {}
        message = check_export_tier_limits(None)[0]

        for tier in ("free", "Intro", "Asastatser", "Professional"):
            assert tier in message.msg

    def test_core_check_hint_mentions_restarting(self, settings):
        """The trap that produced this: the value is read once, at import.

        Exporting the variable into a shell does nothing for a server already
        running, and that is exactly the state that is hard to spot -- the
        setting looks right everywhere you check it from.
        """
        settings.EXPORT_TIERS_ADDRESSES_LIMIT = {}
        assert "restarted" in check_export_tier_limits(None)[0].hint


class TestChecksAreWiredUp:
    """The module as a whole, rather than either check's logic.

    Every other test here calls a check function directly, which is the right
    way to test what it decides -- and means all of them would still pass if
    Django never ran the checks at all. `CoreConfig.ready()` registers them by
    importing this module, and an import that looks unused is exactly the kind
    of line a tidy-up removes.
    """

    def test_core_checks_are_registered_by_app_ready(self):
        """The `noqa: F401` import in `CoreConfig.ready` is load-bearing.

        Asserting that the registry *contains* them would prove nothing here:
        this module imports `core.checks` at the top to call its functions, so
        the checks are registered before any test runs and the assertion passes
        whatever `ready()` does. I wrote that version first and it passed with
        the import deleted.

        What is testable is the mechanism: drop the module from `sys.modules`,
        run `ready()`, and see whether it comes back. That fails the moment the
        import looks unused to somebody tidying up.
        """
        import sys

        from django.apps import apps

        config = apps.get_app_config("core")
        sys.modules.pop("core.checks", None)

        config.ready()

        assert "core.checks" in sys.modules, (
            "CoreConfig.ready() no longer imports core.checks, so no system "
            "check in it will ever run"
        )

    def test_core_checks_ids_are_unique(self):
        """Two checks shared `asastats.W002`, and that is worse than untidy.

        `SILENCED_SYSTEM_CHECKS` keys on the id, so silencing the token's
        expiry nag also silenced the export-limits warning -- one deployment
        quieting a message it had already acted on would lose an unrelated one
        it had never seen. Found by reading, not by any test, which is why
        there is now a test.
        """
        source = (Path(__file__).resolve().parents[1] / "checks.py").read_text()
        ids = re.findall(r'id=f"\{ID_PREFIX\}\.(\w+)"', source)

        assert ids, "no check ids found -- has the id format changed?"
        assert len(ids) == len(set(ids)), (
            f"duplicate check ids: {sorted({i for i in ids if ids.count(i) > 1})}. "
            "Ids are how SILENCED_SYSTEM_CHECKS addresses a message, so two "
            "checks sharing one cannot be silenced independently."
        )

    def test_core_checks_ids_carry_the_project_prefix(self):
        """Keeps them out of Django's own `models.W042`-style namespace."""
        from django.conf import settings

        settings.EXPORT_TIERS_ADDRESSES_LIMIT = {}
        for message in check_export_tier_limits(None):
            assert message.id.startswith(f"{ID_PREFIX}.")


class TestExportTierLimitsDefaults:
    """The arm that fires only if the built-in defaults change."""

    def test_core_check_is_silent_when_the_defaults_permit_exporting(
        self, settings, monkeypatch
    ):
        """No warning to give if the fallbacks stopped being restrictive.

        The check exists because `_DEFAULT_LIMITS` allows every tier below
        Cluster *zero* addresses, so an unset variable silently disables CSV
        export. Were those defaults ever relaxed, the warning would be telling
        people about a problem they no longer have -- so it is derived from the
        defaults rather than assuming them.
        """
        settings.EXPORT_TIERS_ADDRESSES_LIMIT = {}
        monkeypatch.setattr(
            "core.exportpermissions._DEFAULT_LIMITS",
            {"free": 5, "Intro": 5, "Asastatser": 5, "Professional": 5, "Cluster": 10},
        )

        assert check_export_tier_limits(None) == []

    def test_core_check_still_warns_when_one_tier_is_blocked(
        self, settings, monkeypatch
    ):
        """Guard the guard: the silence above must be about the defaults.

        Without this, the test above would also pass if the check had simply
        stopped working.
        """
        settings.EXPORT_TIERS_ADDRESSES_LIMIT = {}
        monkeypatch.setattr(
            "core.exportpermissions._DEFAULT_LIMITS",
            {"free": 5, "Intro": 0, "Asastatser": 5, "Professional": 5, "Cluster": 10},
        )

        messages = check_export_tier_limits(None)

        assert _ids(messages) == [f"{ID_PREFIX}.W003"]
        assert "Intro" in messages[0].msg
        assert "free" not in messages[0].msg
